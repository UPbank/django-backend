from django.db import migrations, transaction


def add_default_accounts(apps, schema_editor):
	Account = apps.get_model('banking', 'Account')
	default_accounts = [
		{'name': '__UPBANK__', 'balance':0},
		{'name' : '__OUTBOUND_TRANSFER__', 'balance':0},
		{'name' : '__INBOUND_TRANSFER__', 'balance':0},
		{'name' : '__GOVERNMENT_PAYMENT_', 'balance':0},
		{'name' : '__SERVICE_PAYMENT__', 'balance':0}
	]
	with transaction.atomic():
		for account in default_accounts:
			Account.objects.create(full_name=account['name'], balance=account['balance'])

class Migration(migrations.Migration):

	dependencies = [
		('banking', '0002_telcoproviders'),
	]

	operations = [
		migrations.RunPython(add_default_accounts),
	]