import datetime

from rest_framework import serializers, validators

from .models import Account, Address, Transfer

from django.conf import settings
from django.apps import apps
from django.db import transaction

from django.contrib.auth.password_validation import validate_password

from .validators import clean_postalcode, clean_taxnumber, clean_birthdate, clean_invalid_characters

# Load user model
User = apps.get_model(settings.AUTH_USER_MODEL)

class AddressSerializer(serializers.ModelSerializer):
	class Meta:
		model = Address
		fields = ['line_one', 'line_two', 'postal_code', 'city', 'district']
	
	def create(self, validated_data):
		clean_postalcode(validated_data['postal_code'])
		return super().create(validated_data)

class AccountSerializer(serializers.ModelSerializer):
	address = AddressSerializer(required=True)
	user = serializers.PrimaryKeyRelatedField(read_only=True)
	balance = serializers.IntegerField(read_only=True)
	email = serializers.EmailField(
					write_only=True,
					required=True,
					validators=[validators.UniqueValidator(queryset=User.objects.all())]
	)
	full_name = serializers.CharField(required=True, validators=[clean_invalid_characters])
	password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
	tax_number = serializers.CharField(required=True, validators=[clean_taxnumber])
	birthdate = serializers.DateField(required=True, validators=[clean_birthdate])
	id_number = serializers.CharField(read_only=True)

	class Meta:
		model = Account
		fields = ['id', 'email', 'password', 'full_name', 'birthdate', 'address', 'tax_number', 'id_number', 'balance', 'created_at', 'user']
	
	def create(self, validated_data):
		with transaction.atomic():
			address_data = validated_data.pop('address')
			address = AddressSerializer().create(address_data)

			user = User.objects.create(email=validated_data.pop('email'),username=validated_data['full_name'])
			user.set_password(validated_data.pop('password'))
			user.save()

			account = Account.objects.create(**validated_data)
			upbank = Account.objects.get(full_name='__UPBANK__')
			Transfer.objects.create(sender=upbank, receiver=account, amount=10000, metadata={'type' : 'WELCOMEGIFT'})
			return account


class TransferSerializer(serializers.Serializer):
	sender_name = serializers.CharField(source='sender.full_name')
	receiver_name = serializers.CharField(source='receiver.full_name')
	sender = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())
	receiver = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())
	amount = serializers.IntegerField()
	metadata = serializers.JSONField()
	notes = serializers.CharField(max_length=255, allow_blank=True, allow_null=True)
	date = serializers.DateTimeField(default=datetime.datetime.now())
	
	class Meta:
		model = Transfer
		fields = ['date', 'sender_name', 'receiver_name', 'sender', 'receiver', 'amount', 'metadata', 'notes']
	