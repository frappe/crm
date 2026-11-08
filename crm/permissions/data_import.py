# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe

CRM_IMPORT_DOCTYPES = ("CRM Lead", "CRM Deal", "CRM Organization", "CRM Task", "CRM Call Log")
IMPORT_DOCTYPES = (*CRM_IMPORT_DOCTYPES, "Contact")
SALES_ROLES = ("Sales Manager", "Sales User")


def get_permission_query_conditions(user: str | None = None) -> str:
	user = user or frappe.session.user
	if _is_unrestricted(user):
		return ""

	doctypes = ", ".join(frappe.db.escape(dt) for dt in IMPORT_DOCTYPES)
	conditions = f"`tabData Import`.`reference_doctype` in ({doctypes})"
	if _is_sales_user_only(user):
		conditions += f" and `tabData Import`.`owner` = {frappe.db.escape(user)}"
	return conditions


def has_permission(doc, ptype: str, user: str | None = None) -> bool:
	user = user or frappe.session.user
	if _is_unrestricted(user):
		return True

	if doc.reference_doctype and doc.reference_doctype not in IMPORT_DOCTYPES:
		return False

	if ptype == "create" or doc.is_new() or not _is_sales_user_only(user):
		return True
	return doc.owner == user


def _is_unrestricted(user: str) -> bool:
	"""Users who reach Data Import through a role other than the sales roles keep their full access."""
	if user == "Administrator":
		return True
	other_roles = {
		perm.role
		for perm in frappe.get_meta("Data Import").permissions
		if perm.read and not perm.permlevel and perm.role not in SALES_ROLES
	}
	return bool(other_roles.intersection(frappe.get_roles(user)))


def _is_sales_user_only(user: str) -> bool:
	return "Sales Manager" not in frappe.get_roles(user)
