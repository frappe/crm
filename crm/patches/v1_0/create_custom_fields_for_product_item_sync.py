import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	if not frappe.db.get_single_value("ERPNext CRM Settings", "enabled"):
		return

	custom_fields = {
		"CRM Product": [
			{
				"fieldname": "erpnext_item_code",
				"fieldtype": "Data",
				"label": "Item Code in ERPNext",
				"read_only": 1,
				"insert_after": "product_code",
			}
		]
	}
	if frappe.db.exists("DocType", "Item"):
		custom_fields["Item"] = [
			{
				"fieldname": "crm_product_code",
				"fieldtype": "Data",
				"label": "CRM Product",
				"read_only": 1,
				"no_copy": 1,
				"insert_after": "item_code",
			}
		]
	create_custom_fields(custom_fields, ignore_validate=True)

	# Latest ERPNext removed the create_custom_fields_for_frappe_crm API and creates its own
	# fields automatically so we no longer call into ERPNext here.
	frappe.get_single("ERPNext CRM Settings").create_custom_fields_in_frappe_crm()
