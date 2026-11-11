# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""A CRM form's route. Frappe serves a published Web Form at /<route> as well as /crm-form/<route>."""

import os
import re

import frappe
from frappe import _
from frappe.utils import cstr
from frappe.website.page_renderers.document_page import DocumentPage
from frappe.website.router import get_doctypes_with_web_view

# Served by the framework itself, not by a `www` page or a route rule.
FRAMEWORK_ROUTES = frozenset({"api", "app", "apps", "assets", "desk", "files", "private"})


def form_route(route: str | None) -> str:
	"""`route` as the builder slugs it. Refuses an empty route and one that another page owns."""
	slug = re.sub(r"[^a-z0-9]+", "-", cstr(route).strip().lower()).strip("-")
	if not slug:
		frappe.throw(_("A form needs a route."), title=_("Route required"))
	if slug in reserved_routes() or web_view_serves(slug):
		frappe.throw(
			_(
				"The route {0} is reserved: the site already serves a page there. Choose another route."
			).format(frappe.bold(slug)),
			title=_("Reserved Route"),
		)
	return slug


def reserved_routes() -> set[str]:
	"""Top-level paths that the framework, a `www` page or a website route rule serves."""
	reserved = set(FRAMEWORK_ROUTES)
	for app in frappe.get_installed_apps():
		www = frappe.get_app_path(app, "www")
		if os.path.isdir(www):
			reserved.update(os.path.splitext(entry)[0] for entry in os.listdir(www))
	for rule in frappe.get_hooks("website_route_rules"):
		first = rule["from_route"].strip("/").partition("/")[0]
		if first and not first.startswith("<"):
			reserved.add(first)
	return reserved


def web_view_serves(slug: str) -> bool:
	"""Whether a published web-view record, such as a Web Page, serves /<slug> or a path below it.
	The Web Form resolves before those records, so the form would take over their URLs."""
	for doctype in get_doctypes_with_web_view():
		meta = frappe.get_meta(doctype)
		if meta.is_virtual or not meta.has_field("route"):
			continue
		filters = {}
		if condition_field := DocumentPage.get_condition_field(meta):
			filters[condition_field] = 1
		or_filters = [["route", "=", slug], ["route", "like", f"{slug}/%"]]
		if frappe.get_all(doctype, filters=filters, or_filters=or_filters, limit=1):
			return True
	return False
