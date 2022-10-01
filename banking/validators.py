from rest_framework import serializers
from .validators_pt import controlNIF
from dateutil.relativedelta import relativedelta
import datetime

def clean_postalcode(postal_code):
	if not isinstance(postal_code, str):
		raise serializers.ValidationError('errors.invalid_postal_code')
	parts = postal_code.split('-')
	if len(parts) != 2:
		raise serializers.ValidationError("errors.invalid_postal_code")
	if len(parts[0]) != 4:
		raise serializers.ValidationError("errors.invalid_postal_code")
	if len(parts[1]) != 3:
		raise serializers.ValidationError("errors.invalid_postal_code")
	
	try:
		int(parts[0])
		int(parts[1])
	except ValueError as e:
		raise serializers.ValidationError("errors.invalid_postal_code") from e

def clean_taxnumber(tax_number):
	'''Given a tax number as an int, validate the tax number against the portuguese strandard'''
	try:
		if not controlNIF(tax_number):
			raise serializers.ValidationError("errors.invalid_tax_number")

	except ValueError as e:
		raise serializers.ValidationError("errors.invalid_tax_number") from e

def clean_birthdate(birthdate):
	if birthdate is not None:
		'''Ensure user is more than 18 years old'''
		if birthdate > datetime.date.today() - relativedelta(years=18):
			raise serializers.ValidationError("errors.underage")
	else:
		raise serializers.ValidationError("errors.no_age")

def clean_invalid_characters(string):
	if '_' in string:
		raise serializers.ValidationError("errors.illegal_character")