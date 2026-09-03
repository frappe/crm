import frappe


def execute():
	"""Facebook leads now arrive only through the Meta integration (OAuth +
	webhook + reconciliation): the old pasted-token polling source is gone."""
	frappe.db.set_value(
		"Failed Lead Sync Log", {"source": ["is", "set"]}, "source", None, update_modified=False
	) if frappe.db.has_column("Failed Lead Sync Log", "source") else None

	if frappe.db.exists("DocType", "Lead Sync Source"):
		frappe.delete_doc("DocType", "Lead Sync Source", force=True, ignore_missing=True)
