# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe

from crm.api.booking import list_services

no_cache = 1


def get_context(context):
	context.no_cache = 1
	context.services = list_services()
	context.org_name = (
		frappe.db.get_single_value("Website Settings", "app_name")
		or frappe.db.get_single_value("System Settings", "app_name")
		or "Booking"
	)
	return context
