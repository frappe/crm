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

	if frappe.db.get_single_value("ERPNext CRM Settings", "is_erpnext_in_different_site"):
		return

	try:
		from erpnext.crm.frappe_crm_api import create_custom_fields_for_frappe_crm
	except ImportError:
		return
	create_custom_fields_for_frappe_crm()
