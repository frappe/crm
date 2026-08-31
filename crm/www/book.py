# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe

no_cache = 1


def get_context(context):
	route = resolve_route()
	name = frappe.db.get_value("CRM Booking Calendar", {"route": route, "enabled": 1})
	if not name:
		raise frappe.DoesNotExistError

	cal = frappe.get_doc("CRM Booking Calendar", name)
	context.no_cache = 1
	# guests POST without CSRF, but a logged-in user browsing the page needs the token
	try:
		context.csrf_token = frappe.sessions.get_csrf_token()
	except Exception:
		context.csrf_token = ""
	context.route = cal.route
	context.title = cal.calendar_name
	context.description = cal.description or ""
	context.duration = cal.duration
	context.location = cal.location or ""
	# a ?token=... query switches the page into manage mode (reschedule/cancel);
	# the token itself is validated by the guest API, never here
	context.manage_token = frappe.form_dict.get("token") or ""
	return context


def resolve_route() -> str:
	route = frappe.form_dict.get("route") or ""
	if not route and (path := frappe.local.request.path):
		parts = [p for p in path.split("/") if p]
		if len(parts) >= 2 and parts[0] == "book":
			route = parts[1]
	return route
