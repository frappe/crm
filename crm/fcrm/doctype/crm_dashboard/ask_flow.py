# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _

APPROVAL_MODE = "Ask"


def flow_available() -> bool:
	"""Frappe v16 has no Flow, and only a Flow User or a System Manager may start a chat.
	CRM gives Flow User to everyone who joins it."""
	try:
		from frappe.flow import is_enabled
	except ImportError:
		return False
	return is_enabled() and frappe.has_permission("Flow Session", "create")


def start_flow_chat(message: str) -> str:
	if not flow_available():
		frappe.throw(_("Flow is not set up on this site"))
	if not (message or "").strip():
		frappe.throw(_("Tell Flow what you want to get done"))

	from frappe.flow.api import create_session, run

	session = create_session(approval_mode=APPROVAL_MODE)["name"]
	run(session, message)
	return session
