from rest_framework import exceptions
from .validators_pt import controlIBAN, controlNIF
from dateutil.relativedelta import relativedelta
import datetime

def clean_postalcode(postal_code):
	if not isinstance(postal_code, str):
		raise exceptions.ValidationError('errors.invalid_postal_code')
	parts = postal_code.split('-')
	if len(parts) != 2:
		raise exceptions.ValidationError("errors.invalid_postal_code")
	if len(parts[0]) != 4:
		raise exceptions.ValidationError("errors.invalid_postal_code")
	if len(parts[1]) != 3:
		raise exceptions.ValidationError("errors.invalid_postal_code")
	
	try:
		int(parts[0])
		int(parts[1])
	except ValueError as e:
		raise exceptions.ValidationError("errors.invalid_postal_code") from e

def clean_taxnumber(tax_number):
	'''Given a tax number as an int, validate the tax number against the portuguese standard'''
	try:
		if not controlNIF(tax_number):
			raise exceptions.ValidationError("errors.invalid_tax_number")

	except ValueError as e:
		raise exceptions.ValidationError("errors.invalid_tax_number") from e

def clean_iban(tax_number):
	'''Given an IBAN as a string, validate the IBAN against the portuguese standard'''
	try:
		if not controlIBAN(tax_number):
			raise exceptions.ValidationError("errors.invalid_iban")

	except ValueError as e:
		raise exceptions.ValidationError("errors.invalid_iban") from e

def clean_birthdate(birthdate):
	if birthdate is not None:
		'''Ensure user is more than 18 years old'''
		if birthdate > datetime.date.today() - relativedelta(years=18):
			raise exceptions.ValidationError("errors.underage")
	else:
		raise exceptions.ValidationError("errors.no_age")

def clean_invalid_characters(string):
	if '_' in string:
		raise exceptions.ValidationError("errors.illegal_character")