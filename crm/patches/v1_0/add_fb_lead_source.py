import frappe


def execute():
	frappe.get_doc({"doctype": "CRM Lead Source", "source_name": "Facebook"}).insert(ignore_if_duplicate=True)
