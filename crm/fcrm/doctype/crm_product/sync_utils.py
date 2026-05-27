import frappe


def payload_differs(payload: dict, target: dict) -> bool:
	"""True if any field in payload has a meaningfully different value in target."""
	for key, new_value in payload.items():
		if (new_value or None) != (target.get(key) or None):
			return True
	return False


def same_site_sync_active() -> bool:
	"""Product sync runs only when integration is enabled AND same-site."""
	settings = frappe.get_cached_doc("ERPNext CRM Settings")
	return bool(settings.enabled) and not settings.is_erpnext_in_different_site
