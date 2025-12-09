# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# License: AGPLv3. See LICENSE

import frappe


def execute():
	"""
	Add custom_order_history field to CRM Lead and CRM Deal
	"""
	
	# Add to CRM Lead
	if not frappe.db.exists("Custom Field", {"dt": "CRM Lead", "fieldname": "custom_order_details_tab"}):
		frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "CRM Lead",
			"label": "Order Details",
			"fieldname": "custom_order_details_tab",
			"fieldtype": "Tab Break",
			"insert_after": "log_tab"
		}).insert(ignore_permissions=True)
	
	if not frappe.db.exists("Custom Field", {"dt": "CRM Lead", "fieldname": "custom_order_history"}):
		frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "CRM Lead",
			"label": "Order History",
			"fieldname": "custom_order_history",
			"fieldtype": "Table",
			"options": "CRM Lead Order Item",
			"insert_after": "custom_order_details_tab"
		}).insert(ignore_permissions=True)
	
	# Add to CRM Deal
	if not frappe.db.exists("Custom Field", {"dt": "CRM Deal", "fieldname": "custom_order_details_tab"}):
		frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "CRM Deal",
			"label": "Order Details",
			"fieldname": "custom_order_details_tab",
			"fieldtype": "Tab Break",
			"insert_after": "log_tab"
		}).insert(ignore_permissions=True)
	
	if not frappe.db.exists("Custom Field", {"dt": "CRM Deal", "fieldname": "custom_order_history"}):
		frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "CRM Deal",
			"label": "Order History",
			"fieldname": "custom_order_history",
			"fieldtype": "Table",
			"options": "CRM Deal Order Item",
			"insert_after": "custom_order_details_tab"
		}).insert(ignore_permissions=True)
	
	frappe.db.commit()

