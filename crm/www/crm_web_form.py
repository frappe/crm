# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe

no_cache = 1


def get_context(context):
	route = resolve_route()
	name = frappe.db.get_value("CRM Web Form", {"route": route, "published": 1})
	# let logged-in authors preview an unpublished (draft) form; guests only see published
	if not name and frappe.session.user != "Guest" and frappe.has_permission("CRM Web Form", "read"):
		name = frappe.db.get_value("CRM Web Form", {"route": route})
	if not name:
		raise frappe.DoesNotExistError

	doc = frappe.get_doc("CRM Web Form", name)
	set_embedding_headers(doc)
	context.no_cache = 1
	try:
		context.csrf_token = frappe.sessions.get_csrf_token()
	except Exception:
		context.csrf_token = ""
	context.draft_preview = not doc.published
	context.form_title = doc.title
	context.form_description = doc.description or ""
	context.form_route = doc.route
	context.submit_label = doc.submit_button_label or "Submit"
	context.success_message = doc.success_message or "Thank you!"
	context.fields = [
		{
			"fieldname": f.fieldname,
			"label": f.label or f.fieldname,
			"fieldtype": f.fieldtype,
			"options": f.options or "",
			"reqd": int(f.reqd or 0),
			"placeholder": f.placeholder or "",
			"description": f.field_description or "",
		}
		for f in doc.fields
	]
	context.layout = build_layout(context.fields)
	return context


def set_embedding_headers(doc):
	"""Allow this page to be embedded as an iframe on the form's allow-listed origins.

	Emits a Content-Security-Policy `frame-ancestors` header. Modern browsers ignore
	the default `X-Frame-Options: SAMEORIGIN` (set by nginx) whenever `frame-ancestors`
	is present, so this is what makes cross-origin embedding work — without it a form
	can only be embedded on its own site.
	"""
	domains = (doc.allowed_embedding_domains or "").split()
	if not domains:
		return
	frappe.local.response_headers["Content-Security-Policy"] = "frame-ancestors 'self' " + " ".join(domains)


def build_layout(fields):
	"""Group fields into sections -> columns using Section/Column Break rows."""
	sections = []
	current = {"label": None, "columns": [[]]}
	for f in fields:
		ft = f["fieldtype"]
		if ft == "Section Break":
			sections.append(current)
			current = {"label": f.get("label") or None, "columns": [[]]}
		elif ft == "Column Break":
			current["columns"].append([])
		else:
			current["columns"][-1].append(f)
	sections.append(current)
	return [s for s in sections if s["label"] or any(col for col in s["columns"])]


def resolve_route() -> str:
	"""The public slug, from the /crm-form/<route> path rule (with a path fallback)."""
	route = (frappe.form_dict.get("route") or "").strip("/")
	if route and route != "crm-form":
		return route
	path = (getattr(frappe.request, "path", "") or "").strip("/")
	prefix = "crm-form/"
	return path[len(prefix) :] if path.startswith(prefix) else path
