import frappe
from frappe.model.rename_doc import rename_doc


def execute():
	if frappe.db.exists("DocType", "Twilio Settings"):
		frappe.flags.ignore_route_conflict_validation = True
		rename_doc("DocType", "Twilio Settings", "CRM Twilio Settings")
		frappe.flags.ignore_route_conflict_validation = False

		frappe.reload_doctype("CRM Twilio Settings", force=True)

	if frappe.db.exists("__Auth", {"doctype": "Twilio Settings"}):
		Auth = frappe.qb.DocType("__Auth")
		result = frappe.qb.from_(Auth).select("*").where(Auth.doctype == "Twilio Settings").run(as_dict=True)

		for row in result:
			frappe.qb.into(Auth).insert(
				"CRM Twilio Settings", "CRM Twilio Settings", row.fieldname, row.password, row.encrypted
			).run()
