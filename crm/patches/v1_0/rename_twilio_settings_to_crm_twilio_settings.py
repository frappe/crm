import frappe
from frappe.model.rename_doc import rename_doc


def execute():
	if frappe.db.table_exists("Twilio Settings"):
		frappe.flags.ignore_route_conflict_validation = True
		rename_doc("DocType", "Twilio Settings", "CRM Twilio Settings")
		frappe.flags.ignore_route_conflict_validation = False

		frappe.reload_doctype("CRM Twilio Settings", force=True)
