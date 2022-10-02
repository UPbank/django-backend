from django.db import models
from django.conf import settings

class Account(models.Model):
	'''Validate that user is 18 years old or older'''
	full_name = models.CharField(max_length=80)
	birthdate = models.DateField(blank=True, null=True)
	address = models.OneToOneField('Address', related_name='account', on_delete=models.CASCADE, blank=True, null=True)
	tax_number = models.CharField(max_length=80, blank=True, null=True) # Char to support foreign tax numbers when manually registring
	id_number = models.CharField(max_length=80, blank=True, null=True) # Char to support foreign ID numbers when manually registring
	balance = models.PositiveBigIntegerField(default=0)
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)

	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.full_name

class Address(models.Model):
	line_one = models.CharField(max_length=80)
	line_two = models.CharField(max_length=80, blank=True, null=True)
	postal_code = models.CharField(max_length=80) # Char to support foreign postal codes when manually registring
	city = models.CharField(max_length=80)
	district = models.CharField(max_length=80)

class TelcoProvider(models.Model):
	name = models.CharField(max_length=80)
	account = models.ForeignKey('Account', related_name='+', on_delete=models.PROTECT)

	def __str__(self):
		return self.name

class Card(models.Model):
	name = models.CharField(max_length=80)
	expiry_date = models.DateField()
	cvv = models.SmallIntegerField()
	pin_code = models.PositiveSmallIntegerField()
	online_payments = models.BooleanField(default=True)
	nfc_payments = models.BooleanField(default=True)
	account = models.ForeignKey(Account, on_delete=models.CASCADE)

	def __str__(self):
		return self.name

class Transfer(models.Model):
	date = models.DateTimeField(auto_now_add=True)
	sender = models.ForeignKey(Account, related_name='expenses', on_delete=models.PROTECT)
	receiver = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='income')
	amount = models.PositiveBigIntegerField()
	metadata = models.JSONField()
	notes = models.CharField(max_length=255, blank=True, null=True)

class DirectDebit(models.Model):
	active = models.BooleanField()
	date = models.DateField()
	receiver = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='+')
	sender = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='direct_debits')
	last_debit = models.ForeignKey(Transfer, on_delete=models.PROTECT, related_name='+')

class StandingOrder(models.Model):
	class Frequency(models.TextChoices):
		DAILY = 'DAILY'
		WEEKLY = 'WEEKLY'
		MONTHLY = 'MONTHLY'
		YEARLY = 'YEARLY'
	# date = models.DateField() # TODO: Allow setting a date in the future instead of the day the transfer is being made
	frequency = models.CharField(max_length=7, choices=Frequency.choices)
	sender = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='standing_orders')
	receiver = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='+')
	amount = models.PositiveBigIntegerField()
	last_debit = models.ForeignKey(Transfer, on_delete=models.PROTECT, related_name='+', blank=True, null=True)
	metadata = models.JSONField()