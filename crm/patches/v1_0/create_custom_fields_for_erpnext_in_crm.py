import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	enabled = frappe.db.get_single_value("ERPNext CRM Settings", "enabled")
	if enabled:
		custom_fields = {
			"CRM Deal": [
				{
					"fieldname": "erpnext_customer",
					"fieldtype": "Data",
					"label": "Customer in ERPNext",
					"insert_after": "lead_name",
				}
			]
		}
		create_custom_fields(custom_fields, ignore_validate=True)
