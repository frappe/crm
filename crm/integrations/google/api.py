# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Settings-modal API for the Google Calendar connection."""

import frappe
from frappe import _

from crm.integrations.google.oauth import client_id, client_secret, is_managed


@frappe.whitelist()
def get_status() -> dict:
	"""State of the current user's calendar link, for the Connect button."""
	name = frappe.db.get_value("Google Calendar", {"user": frappe.session.user})
	connected = False
	if name:
		try:
			connected = bool(
				frappe.get_doc("Google Calendar", name).get_password("refresh_token", raise_exception=False)
			)
		except Exception:
			connected = False

	return {
		"can_connect": bool(client_id() and client_secret()),
		"managed": is_managed(),
		"name": name,
		"connected": connected,
	}


@frappe.whitelist(methods=["POST"])
def disconnect() -> dict:
	"""Unlink this user's calendar. The events already in Google stay there."""
	name = frappe.db.get_value("Google Calendar", {"user": frappe.session.user})
	if not name:
		return get_status()
	doc = frappe.get_doc("Google Calendar", name)
	if doc.user != frappe.session.user:
		frappe.throw(_("This calendar belongs to another user"), frappe.PermissionError)
	doc.refresh_token = ""
	doc.enabled = 0
	doc.save(ignore_permissions=True)
	return get_status()
