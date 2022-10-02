import luhn

from banking.validators_pt import generateControlNIB

_iban_prefix = "PT50"
_nib_prefix = "00972890"
_card_prefix = "436339"

def id_to_iban(id):
	"""Converts a given ID to an IBAN."""
	checksum = str(generateControlNIB(_nib_prefix + str(id).zfill(11)))
	return _iban_prefix + _nib_prefix + str(id).zfill(11) + str(checksum).zfill(2)

def id_to_card_number(id):
	"""Converts a given ID to a card number."""
	return luhn.append((_card_prefix + str(id).zfill(9)))