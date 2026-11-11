import frappe

from crm.api.form import GUEST_SELECT_REFUSED


def execute():
	"""Before frappe/crm#3403, the forms builder's Grant Access could give Guest `select` on these
	doctypes, which lets an anonymous visitor list record names through the REST API."""
	for doctype in GUEST_SELECT_REFUSED:
		frappe.db.delete("Custom DocPerm", {"parent": doctype, "role": "Guest"})
		frappe.clear_cache(doctype=doctype)
