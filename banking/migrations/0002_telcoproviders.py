from django.db import migrations, transaction


def add_telcoproviders(apps, schema_editor):
	TelcoProvider = apps.get_model('banking', 'TelcoProvider')
	Account = apps.get_model('banking', 'Account')
	providers = [
		'Lycamobile GT Mobile',
		'MEO',
		'MEO Card',
		'MEO Card - PT Hello / PT Card',
		'MEO Card - Telefone Hello',
		'MEO Escola Digital',
		'Moche',
		'NOS',
		'NOS - Escola Digital',
		'SAPO',
		'Sapo ADSL',
		'UZO',
		'Via Card',
		'Vodafone',
		'WTF'
	]
	with transaction.atomic():
		for provider in providers:
			account = Account.objects.create(full_name=provider, balance=0)
			TelcoProvider.objects.create(name=provider, account=account)

class Migration(migrations.Migration):

	dependencies = [
		('banking', '0001_initial'),
	]

	operations = [
		migrations.RunPython(add_telcoproviders),
	]