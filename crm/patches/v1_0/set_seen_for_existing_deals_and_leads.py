import json

import frappe
from frappe.query_builder import DocType

from crm.api.session import CRM_ALLOWED_ROLES

DOCTYPES = ("CRM Deal", "CRM Lead")


def execute():
	"""Backfill `_seen` for CRM Deals/Leads that predate track_seen being enabled.

	Without this, every record created before track_seen was turned on would
	show up as unvisited (bold) to everyone, since there's no real view
	history to reconstruct. Default them to already seen by every enabled
	CRM user instead, so only records created or updated from now on show
	as unvisited.
	"""
	users = get_crm_users()
	if not users:
		return

	seen = json.dumps(users)

	for doctype in DOCTYPES:
		table = DocType(doctype)
		frappe.qb.update(table).set(table._seen, seen).where(
			table._seen.isnull() | table._seen.isin(["", "[]"])
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
