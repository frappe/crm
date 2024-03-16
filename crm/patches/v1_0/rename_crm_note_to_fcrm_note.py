import frappe
from frappe.model.rename_doc import rename_doc


def execute():
	if frappe.db.exists("DocType", "FCRM Note"):
		return

	frappe.flags.ignore_route_conflict_validation = True
	rename_doc("DocType", "CRM Note", "FCRM Note")
	frappe.flags.ignore_route_conflict_validation = False

	frappe.reload_doctype("FCRM Note", force=True)