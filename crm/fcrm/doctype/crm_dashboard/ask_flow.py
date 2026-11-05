# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _

FLOW_ROLE = "Flow User"
APPROVAL_MODE = "Ask"


def flow_available() -> bool:
	"""Frappe v16 has no Flow, and a site without a provider has nothing to answer with."""
	return bool(
		frappe.db.exists("DocType", "Flow Session") and frappe.db.exists("Flow Provider", {"enabled": 1})
	)


def start_flow_chat(message: str) -> str:
	if not flow_available():
		frappe.throw(_("Flow is not set up on this site"))
	if not (message or "").strip():
		frappe.throw(_("Tell Flow what you want to get done"))

	grant_flow_role(frappe.session.user)

	from frappe.flow.api import create_session, run

	session = create_session(approval_mode=APPROVAL_MODE)["name"]
	run(session, message)
	return session


def grant_flow_role(user: str):
	if FLOW_ROLE in frappe.get_roles(user):
		return
	doc = frappe.get_doc("User", user)
	doc.append("roles", {"role": FLOW_ROLE})
	doc.flags.ignore_permissions = True
	doc.save()
	frappe.clear_cache(user=user)
