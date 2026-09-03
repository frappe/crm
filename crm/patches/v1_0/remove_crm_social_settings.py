import frappe


def execute():
	"""Social publishing now runs only on the Meta connection: the provider
	settings single (Postiz/Ayrshare credentials) is gone."""
	if frappe.db.exists("DocType", "CRM Social Settings"):
		frappe.delete_doc("DocType", "CRM Social Settings", force=True, ignore_missing=True)
