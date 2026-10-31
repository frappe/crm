import frappe

from crm.install import add_sales_manager_setup_permissions


def execute():
	add_sales_manager_setup_permissions()
	remove_sales_user_holiday_list_permissions()


def remove_sales_user_holiday_list_permissions():
	"""The doctype's own rows dropped Sales User; this drops a site's customised copy of them too."""
	frappe.db.delete("Custom DocPerm", {"parent": "CRM Holiday List", "role": "Sales User"})
	frappe.clear_cache(doctype="CRM Holiday List")
