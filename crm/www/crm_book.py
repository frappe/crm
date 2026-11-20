# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe

from crm.api.booking import booking_form, get_page, public_page
from crm.www.crm_form import form_fields_context, set_embedding_headers

no_cache = 1


def get_context(context):
	page = get_page(resolve_route())
	set_embedding_headers(page)
	context.no_cache = 1
	# ?embed=1 (set by the iframe snippet) drops the page chrome, as on web forms
	context.embed = frappe.form_dict.get("embed") in ("1", "true", "yes")
	try:
		context.csrf_token = frappe.sessions.get_csrf_token()
	except Exception:
		context.csrf_token = ""
	context.page_data = public_page(page)
	form = booking_form(page)
	context.update(form_fields_context(form) if form else {"fields": [], "layout": [], "link_options": {}})
	context.draft_preview = not page.enabled
	return context


def resolve_route() -> str:
	"""The public slug, from the /crm-book/<route> path rule (with a path fallback)."""
	route = (frappe.form_dict.get("route") or "").strip("/")
	if route and route != "crm-book":
		return route
	path = (getattr(frappe.request, "path", "") or "").strip("/")
	prefix = "crm-book/"
	return path[len(prefix) :] if path.startswith(prefix) else path
