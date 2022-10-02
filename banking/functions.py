import luhn

_iban_prefix = "PT5000972890"
_card_prefix = "436339"

def id_to_iban(id):
	"""Converts a given ID to an IBAN."""
	checksum = 98 - (id*100 % 97)
	return _iban_prefix + str(id).zfill(11) + str(checksum).zfill(2)

def id_to_card_number(id):
	"""Converts a given ID to a card number."""
	return luhn.append((_card_prefix + str(id).zfill(9)))