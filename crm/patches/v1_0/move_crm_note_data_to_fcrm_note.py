import frappe
from frappe.model.rename_doc import rename_doc


def execute():

	if not frappe.db.exists("DocType", "FCRM Note"):
		frappe.flags.ignore_route_conflict_validation = True
		rename_doc("DocType", "CRM Note", "FCRM Note")
		frappe.flags.ignore_route_conflict_validation = False

		frappe.reload_doctype("FCRM Note", force=True)

	if frappe.db.exists("DocType", "FCRM Note") and frappe.db.count("FCRM Note") > 0:
		return

	notes = frappe.db.sql("SELECT * FROM `tabCRM Note`", as_dict=True)
	if notes:
		for note in notes:
			doc = frappe.get_doc({
				"doctype": "FCRM Note",
				"creation": note.get("creation"),
				"modified": note.get("modified"),
				"modified_by": note.get("modified_by"),
				"owner": note.get("owner"),
				"title": note.get("title"),
				"content": note.get("content"),
				"reference_doctype": note.get("reference_doctype"),
				"reference_docname": note.get("reference_docname"),
			})
			doc.db_insert()