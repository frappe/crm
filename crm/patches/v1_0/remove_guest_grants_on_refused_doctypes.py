import frappe

from crm.api.form import GUEST_SELECT_REFUSED


def execute():
	"""Before frappe/crm#3403, the forms builder's Grant Access could give Guest `select` on these
	doctypes, which lets an anonymous visitor list record names through the REST API."""
	for doctype in GUEST_SELECT_REFUSED:
		for name in frappe.get_all("Custom DocPerm", {"parent": doctype, "role": "Guest"}, pluck="name"):
			frappe.delete_doc("Custom DocPerm", name, ignore_permissions=True)
		frappe.clear_cache(doctype=doctype)
