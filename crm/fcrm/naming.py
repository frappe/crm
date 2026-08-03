import secrets
import string

_CHARS = string.ascii_uppercase + string.digits  # A-Z 0-9


def generate_random5(doc, series_part):
	"""5-character uppercase alphanumeric suffix for naming series (RANDOM5 token)."""
	return "".join(secrets.choice(_CHARS) for _ in range(5))
