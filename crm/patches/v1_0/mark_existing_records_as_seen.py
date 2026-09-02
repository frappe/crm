import json

import frappe

from crm.api.session import CRM_ALLOWED_ROLES

DOCTYPES = ("CRM Lead", "CRM Deal")


def execute():
	# List views dim records the current user has already opened. Records that
	# existed before this feature have an empty `_seen`, so every one of them
	# would show up as unvisited on upgrade. Mark them as seen by the current
	# CRM users; only records created or updated from now on show as unvisited.
	users = get_crm_users()
	if not users:
		return

	seen = json.dumps(users)

	for doctype in DOCTYPES:
		table = frappe.qb.DocType(doctype)

		(
			frappe.qb.update(table)
			.set(table._seen, seen)
			.where(table._seen.isnull() | table._seen.isin(["", "[]"]))
		).run()


def get_crm_users():
	users_with_crm_role = frappe.get_all(
		"Has Role",
		filters={"parenttype": "User", "role": ["in", CRM_ALLOWED_ROLES]},
		pluck="parent",
		distinct=True,
	)
	users_with_crm_role.append("Administrator")

	return frappe.get_all(
		"User",
		filters={"name": ["in", users_with_crm_role], "enabled": 1},
		pluck="name",
	)
