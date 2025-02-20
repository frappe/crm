import frappe


def execute():
    frappe.db.set_value("CRM Settings", "CRM Settings", "auto_creation_of_contact", 0)
