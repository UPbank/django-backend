from django.db import models
from django.conf import settings

# Create your models here.

class Account(models.Model):
    '''Validate that user is 18 years old or older'''
    full_name = models.CharField(max_length=100, blank=False, null=False)
    birthdate = models.DateField(blank=True, null=True)
    address = models.OneToOneField('Address', related_name='account', on_delete=models.CASCADE, blank=True, null=True)
    tax_number = models.CharField(max_length=100, blank=True, null=True) # Char to support foreign tax numbers when manually registring
    id_number = models.CharField(max_length=100, blank=True, null=True) # Char to support foreign ID numbers when manually registring
    balance = models.PositiveBigIntegerField(default=0, blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.full_name

class Address(models.Model):
    line_one = models.CharField(max_length=100, blank=False, null=False)
    line_two = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=100, blank=False, null=False) # Char to support foreign postal codes when manually registring
    city = models.CharField(max_length=100, blank=False, null=False)
    district = models.CharField(max_length=100, blank=False, null=False)

class TelcoProvider(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False)
    account = models.ForeignKey('Account', related_name='+', on_delete=models.CASCADE, blank=False, null=False)

    def __str__(self):
        return self.name

class Card(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False)
    expiry_date = models.DateField(blank=False, null=False)
    pin_code = models.PositiveIntegerField(blank=False, null=False)
    online_payments = models.BooleanField(blank=False, null=False)
    nfc_payments = models.BooleanField(blank=False, null=False)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, blank=False, null=False)

    def __str__(self):
        return self.name

class Transfer(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    sender = models.ForeignKey(Account, related_name='expenses', on_delete=models.CASCADE, blank=False, null=False)
    receiver = models.ForeignKey(Account, on_delete=models.CASCADE, blank=False, null=False, related_name='income')
    amount = models.PositiveBigIntegerField(blank=False, null=False)
    metadata = models.JSONField(blank=False, null=False)
    notes = models.CharField(max_length=255, blank=True, null=True)

class DirectDebit(models.Model):
    active = models.BooleanField(blank=False, null=False)
    date = models.DateField(blank=False, null=False)
    receiver = models.ForeignKey(Account, on_delete=models.CASCADE, blank=False, null=False, related_name='+')
    sender = models.ForeignKey(Account, on_delete=models.CASCADE, blank=False, null=False, related_name='direct_debits')
    last_debit = models.ForeignKey(Transfer, on_delete=models.CASCADE, blank=False, null=False, related_name='+')

class StandingOrder(models.Model):
    class Frequency(models.TextChoices):
        DAILY = 'DAILY'
        WEEKLY = 'WEEKLY'
        MONTHLY = 'MONTHLY'
        YEARLY = 'YEARLY'
    date = models.DateField(blank=False, null=False)
    frequency = models.CharField(max_length=7, blank=False, null=False, choices=Frequency.choices)
    sender = models.ForeignKey(Account, on_delete=models.CASCADE, blank=False, null=False, related_name='standing_orders')
    receiver = models.ForeignKey(Account, on_delete=models.CASCADE, blank=False, null=False, related_name='+')