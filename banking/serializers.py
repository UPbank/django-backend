import datetime
from dateutil.relativedelta import relativedelta
from random import SystemRandom

from rest_framework import serializers, exceptions, validators

from banking.functions import id_to_card_number, id_to_iban
from .models import Account, Address, Card, DirectDebit, StandingOrder, Transfer, TelcoProvider

from django.conf import settings
from django.apps import apps
from django.db import transaction, models
from django.contrib.auth.password_validation import validate_password

from .validators import clean_postalcode, clean_taxnumber, clean_birthdate, clean_invalid_characters

# Load user model
User = apps.get_model(settings.AUTH_USER_MODEL)

class AddressSerializer(serializers.ModelSerializer):
	postal_code = serializers.CharField(validators=[clean_postalcode])
	class Meta:
		model = Address
		fields = ['line_one', 'line_two', 'postal_code', 'city', 'district']

class AccountSerializer(serializers.ModelSerializer):
	address = AddressSerializer(required=True)
	email = serializers.EmailField(
		write_only=True,
		required=True,
		validators=[validators.UniqueValidator(queryset=User.objects.all())]
	)
	full_name = serializers.CharField(required=True, validators=[clean_invalid_characters])
	password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
	tax_number = serializers.CharField(required=True, validators=[clean_taxnumber])
	id_number = serializers.CharField(required=True, max_length=80)
	birthdate = serializers.DateField(required=True, validators=[clean_birthdate])
	iban = serializers.SerializerMethodField(read_only=True)
	balance = serializers.IntegerField(read_only=True)

	class Meta:
		model = Account
		fields = ['id', 'email', 'password', 'full_name', 'birthdate', 'address', 'tax_number', 'id_number', 'balance', 'iban', 'created_at']
	
	def get_iban(self, obj):
		return id_to_iban(obj.id)
	
	def create(self, validated_data):
		with transaction.atomic():
			address_data = validated_data.pop('address')
			address = AddressSerializer().create(address_data)

			email = validated_data.pop('email')
			user = User.objects.create(email=email, username=email)
			user.set_password(validated_data.pop('password'))
			user.save()

			account = Account.objects.create(**validated_data, address=address, user=user, balance=settings.DEFAULT_BALANCE)
			upbank = Account.objects.get(full_name='__UPBANK__')
			Transfer.objects.create(sender=upbank, receiver=account, amount=settings.DEFAULT_BALANCE, metadata={'type' : 'WELCOMEGIFT'})

			generator = SystemRandom()
			Card.objects.create(account=account, name="__PHYSICAL_CARD__", expiry_date=datetime.datetime.now() + relativedelta(years=2), pin_code=generator.randint(0, settings.MAX_PIN), cvv=generator.randint(0, settings.MAX_CVV))
			Card.objects.create(account=account, name="__VIRTUAL_CARD__", expiry_date=datetime.datetime.now() + relativedelta(years=2), pin_code=generator.randint(0, settings.MAX_PIN), cvv=generator.randint(0, settings.MAX_CVV))
			return account

class TransferSerializer(serializers.Serializer):
	name = serializers.SerializerMethodField(read_only=True)
	sender = serializers.PrimaryKeyRelatedField(read_only=True)
	receiver = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())
	amount = serializers.IntegerField()
	metadata = serializers.JSONField(read_only=True)
	notes = serializers.CharField(max_length=80, allow_blank=True, allow_null=True)
	date = serializers.DateTimeField(read_only=True)
	
	class Meta:
		model = Transfer
		fields = ['date', 'name', 'sender', 'receiver', 'amount', 'metadata', 'notes']
	
	def get_name(self, obj):
		'''If user is sender, get receiver, otherwise get sender'''
		if obj.sender == self.context['request'].user.account:
			return obj.receiver.full_name
		return obj.sender.full_name
	
	def create(self, validated_data):
		with transaction.atomic():
			if 'user' not in self.context['request']:
				raise exceptions.AuthenticationFailed('errors.auth')
			sender = Account.objects.select_for_update().get(user=self.context['request'].user) # Lock sender account to ensure no funny balance business occurs
			if sender.balance < validated_data['amount']:
				raise exceptions.ValidationError('errors.insufficient_balance')
			sender.balance = models.F('balance') - validated_data['amount']
			sender.save()
			
			receiver = validated_data.pop('receiver')
			receiver.balance = models.F('balance') + validated_data['amount']
			receiver.save()
			return Transfer.objects.create(sender=sender, receiver=receiver, **validated_data)

class TransferSerializer(serializers.Serializer):
	name = serializers.SerializerMethodField(read_only=True)
	receiver = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), write_only=True)
	amount = serializers.IntegerField()
	type = serializers.SerializerMethodField(read_only=True)
	metadata = serializers.JSONField(read_only=True)
	notes = serializers.CharField(max_length=80, allow_blank=True, allow_null=True, required=False)
	date = serializers.DateTimeField(read_only=True)
	
	class Meta:
		model = Transfer
		fields = ['date', 'name', 'type', 'amount', 'metadata', 'notes', 'receiver']
	
	def get_name(self, obj):
		'''If user is sender, get receiver, otherwise get sender'''
		if obj.sender == self.context['request'].user.account:
			return obj.receiver.full_name
		return obj.sender.full_name
	
	def get_type(self, obj):
		if obj.sender == self.context['request'].user.account:
			return 'EXPENSE'
		return 'INCOME'
	
	def create(self, validated_data):
		with transaction.atomic():
			sender = Account.objects.select_for_update().get(user=self.context['request'].user) # Lock sender account to ensure no funny balance business occurs
			if sender.balance < validated_data['amount']:
				raise exceptions.ValidationError('errors.insufficient_balance')
			if sender == validated_data['receiver']:
				raise exceptions.ValidationError('errors.transfer_to_self')
			sender.balance = models.F('balance') - validated_data['amount']
			sender.save()
			
			receiver = validated_data.pop('receiver')
			receiver.balance = models.F('balance') + validated_data['amount']
			receiver.save()
			return Transfer.objects.create(sender=sender, receiver=receiver, **validated_data)

class BankTransferSerializer(TransferSerializer):
	iban = serializers.CharField(min_length=25, max_length=25, write_only=True)

	receiver = None # override superclass
	
	class Meta:
		model = Transfer
		fields = ['iban', 'amount', 'notes']
	
	def create(self, validated_data):
		iban = validated_data.pop('iban')
		try:
			receiver = Account.objects.get(id=int(iban[12:23]))
		except Account.DoesNotExist:
			receiver = Account.objects.get(full_name='__BANK_TRANSFER__')
		return super().create({'receiver' : receiver, 'metadata' : {'type' : 'NATIONAL', 'iban' : iban}, **validated_data})

class ServicePaymentSerializer(TransferSerializer):
	entity = serializers.CharField(min_length=5, max_length=5, write_only=True)
	reference = serializers.CharField(min_length=9, max_length=9, write_only=True)

	receiver = None # override superclass
	notes = None # override superclass
	
	class Meta:
		model = Transfer
		fields = ['entity', 'reference', 'amount']
	
	def create(self, validated_data):
		entity = validated_data.pop('entity')
		reference = validated_data.pop('reference')
		receiver = Account.objects.get(full_name='__SERVICE_PAYMENT__')
		return super().create({'receiver' : receiver, 'metadata' : {'type' : 'SERVICE', 'entity' : entity, 'reference' : reference}, **validated_data})

class GovernmentPaymentSerializer(TransferSerializer):
	reference = serializers.CharField(min_length=15, max_length=15, write_only=True)

	receiver = None # override superclass
	notes = None # override superclass
	
	class Meta:
		model = Transfer
		fields = ['reference', 'amount']
	
	def create(self, validated_data):
		reference = validated_data.pop('reference')
		receiver = Account.objects.get(full_name='__GOVERNMENT_PAYMENT__')
		return super().create({'receiver' : receiver, 'metadata' : {'type' : 'GOVERNMENT', 'reference' : reference}, **validated_data})

class TelcoPaymentSerializer(TransferSerializer):
	provider = serializers.PrimaryKeyRelatedField(queryset=TelcoProvider.objects.all(), write_only=True)
	phone_number = serializers.CharField(min_length=9, max_length=9, write_only=True)

	receiver = None # override superclass
	notes = None # override superclass

	allowed_second_digits = ['1', '2', '3', '6']
	
	class Meta:
		model = Transfer
		fields = ['provider', 'phone_number', 'amount']
	
	def create(self, validated_data):
		phone_number = validated_data.pop('phone_number')
		if phone_number[0] != '9' or phone_number[1] not in self.allowed_second_digits:
			raise exceptions.ValidationError('errors.invalid_phone_number')
		receiver = validated_data.pop('provider').account
		return super().create({'receiver' : receiver, 'metadata' : {'type' : 'TELCO', 'phone_number' : phone_number}, **validated_data})

class TelcoProviderSerializer(serializers.ModelSerializer):
	class Meta:
		model = TelcoProvider
		fields = ['id', 'name']

class StandingOrderSerializer(serializers.ModelSerializer):
	iban = serializers.CharField(min_length=25, max_length=25, write_only=True)
	name = serializers.CharField(source='receiver.full_name', read_only=True)
	
	class Meta:
		model = StandingOrder
		fields = ['id', 'iban', 'amount', 'frequency', 'name']
	
	def create(self, validated_data):
		iban = validated_data.pop('iban')
		sender = self.context['request'].user.account
		if sender.standing_orders.count() >= 20:
			raise exceptions.ValidationError('errors.too_many_standing_orders')
		try:
			receiver = Account.objects.get(id=int(iban[12:23]))
			if sender == receiver:
				raise exceptions.ValidationError('errors.transfer_to_self')
		except Account.DoesNotExist:
			receiver = Account.objects.get(full_name='__BANK_TRANSFER__')
		
		return super().create(
			{
				'sender' : sender, 
				'receiver' : receiver, 
				'metadata' : {
					'type' : 'STANDING_ORDER',
					'iban' : iban
				}, 
				**validated_data
			}
		)

class DirectDebitSerializer(serializers.ModelSerializer):
	name = serializers.CharField(source='receiver.full_name', read_only=True)
	class Meta:
		model = DirectDebit
		fields = ['id', 'active', 'name']

class CardSerializer(serializers.ModelSerializer):
	pin_code = serializers.IntegerField(min_value=0, max_value=9999, write_only=True)
	number = serializers.SerializerMethodField(read_only=True)
	cvv = serializers.IntegerField(read_only=True)
	expiry_date = serializers.DateField(read_only=True)

	def get_number(self, obj):
		return id_to_card_number(obj.id)

	class Meta:
		model = Card
		fields = ['id', 'name', 'number', 'expiry_date', 'cvv', 'pin_code', 'online_payments', 'nfc_payments']