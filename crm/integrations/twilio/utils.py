from frappe.utils import get_url


def get_public_url(path: str=None):
	return get_url().split(":8", 1)[0] + path


def merge_dicts(d1: dict, d2: dict):
	"""Merge dicts of dictionaries.
	>>> merge_dicts(
		{'name1': {'age': 20}, 'name2': {'age': 30}},
		{'name1': {'phone': '+xxx'}, 'name2': {'phone': '+yyy'}, 'name3': {'phone': '+zzz'}}
	)
	... {'name1': {'age': 20, 'phone': '+xxx'}, 'name2': {'age': 30, 'phone': '+yyy'}}
	"""
	return {k:{**v, **d2.get(k, {})} for k, v in d1.items()}

def parse_mobile_no(mobile_no: str):
	"""Parse mobile number to remove spaces, brackets, etc.
	>>> parse_mobile_no('+91 (766) 667 6666')
	... '+917666676666'
	"""
	return ''.join([c for c in mobile_no if c.isdigit() or c == '+'])