def payload_differs(payload: dict, target: dict) -> bool:
	"""True if any field in payload has a meaningfully different value in target."""
	for key, new_value in payload.items():
		if (new_value or None) != (target.get(key) or None):
			return True
	return False
