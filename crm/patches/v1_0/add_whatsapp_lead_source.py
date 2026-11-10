import frappe


def execute():
	if frappe.db.exists("CRM Lead Source", "WhatsApp"):
		return
	frappe.get_doc({"doctype": "CRM Lead Source", "source_name": "WhatsApp"}).insert(ignore_permissions=True)
