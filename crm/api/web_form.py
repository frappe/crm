# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Hybrid web form API.

Storage/submission/validation is delegated to Frappe's built-in `Web Form`
doctype; this module only:
  1. curates which target fields a CRM form may collect,
  2. gives the CRM builder a small, scoped CRUD surface over Web Form records,
  3. re-applies CRM-specific enrichment (source, organization, primary contact)
     on submission, which the framework's generic insert does not do.
"""

import json

import frappe
from frappe import _

ALLOWED_DOCTYPES = ("CRM Lead", "CRM Deal")
WEB_FORM_SOURCE = "Web Form"
WEB_FORM_MODULE = "FCRM"


def ensure_web_form_source() -> str:
	"""Return the 'Web Form' CRM Lead Source, creating it once if needed."""
	if not frappe.db.exists("CRM Lead Source", WEB_FORM_SOURCE):
		frappe.get_doc({"doctype": "CRM Lead Source", "source_name": WEB_FORM_SOURCE}).insert(
			ignore_permissions=True
		)
	return WEB_FORM_SOURCE


# Fieldtypes a web form can render/collect. Kept to simple input types for now.
SUPPORTED_FIELDTYPES = (
	"Data",
	"Small Text",
	"Text",
	"Long Text",
	"Select",
	"Int",
	"Float",
	"Currency",
	"Check",
	"Date",
	"Datetime",
	"Phone",
)

# Never expose these as mappable fields even if their type is supported.
DENIED_FIELDNAMES = (
	"naming_series",
	"lead_name",
	"converted",
	"sla_status",
	"response_by",
	"first_response_time",
	"first_responded_on",
	"facebook_form_id",
	"facebook_lead_id",
)


def _check_manager():
	"""CRM forms are managed by CRM managers, not Website Managers. Gate here and
	then write the Web Form with ignore_permissions (the role mismatch, in code)."""
	roles = set(frappe.get_roles())
	if not roles & {"System Manager", "Sales Manager"}:
		frappe.throw(_("Not permitted"), frappe.PermissionError)


@frappe.whitelist()
def get_form_fields(document_type: str) -> list[dict]:
	"""Mappable fields of a target DocType, for the builder's field picker."""
	if document_type not in ALLOWED_DOCTYPES:
		frappe.throw(_("Web forms can only map to: {0}").format(", ".join(ALLOWED_DOCTYPES)))

	meta = frappe.get_meta(document_type)
	fields = []
	for df in meta.fields:
		if df.fieldtype not in SUPPORTED_FIELDTYPES:
			continue
		if not df.fieldname or df.fieldname in DENIED_FIELDNAMES:
			continue
		if df.hidden or df.read_only:
			continue
		fields.append(
			{
				"fieldname": df.fieldname,
				"label": df.label or df.fieldname,
				"fieldtype": df.fieldtype,
				"options": df.options,
				"reqd": df.reqd,
			}
		)
	return fields


@frappe.whitelist()
def list_web_forms() -> list[dict]:
	"""CRM web forms only (native Web Form records mapped to Lead/Deal)."""
	_check_manager()
	return frappe.get_all(
		"Web Form",
		filters={"doc_type": ["in", ALLOWED_DOCTYPES]},
		fields=[
			"name",
			"title",
			"route",
			"doc_type as document_type",
			"crm_published as published",
			"modified",
		],
		order_by="modified desc",
	)


@frappe.whitelist()
def get_web_form_config(name: str) -> dict:
	"""Full config for the builder, read from the native Web Form record."""
	_check_manager()
	doc = frappe.get_doc("Web Form", name)
	if doc.doc_type not in ALLOWED_DOCTYPES:
		frappe.throw(_("Not a CRM web form"))
	return {
		"name": doc.name,
		"title": doc.title,
		"route": doc.route,
		"document_type": doc.doc_type,
		"published": doc.crm_published,
		"submit_button_label": doc.button_label or _("Submit"),
		"description": doc.introduction_text or "",
		"success_message": doc.success_message or "",
		"allowed_embedding_domains": doc.allowed_embedding_domains or "",
		"fields": [
			{
				"fieldname": f.fieldname,
				"label": f.label,
				"fieldtype": f.fieldtype,
				"options": f.options,
				"reqd": f.reqd,
				"placeholder": f.placeholder,
				"field_description": f.description,
			}
			for f in doc.web_form_fields
		],
	}


@frappe.whitelist()
def save_web_form(name: str | None, form: dict | str) -> dict:
	"""Create/update a native Web Form scoped to CRM doctypes."""
	_check_manager()
	if isinstance(form, str):
		form = json.loads(form or "{}")

	if form.get("document_type") not in ALLOWED_DOCTYPES:
		frappe.throw(_("Web forms can only map to: {0}").format(", ".join(ALLOWED_DOCTYPES)))

	doc = frappe.get_doc("Web Form", name) if name else frappe.new_doc("Web Form")
	if name and doc.doc_type not in ALLOWED_DOCTYPES:
		frappe.throw(_("Not a CRM web form"))

	doc.title = form.get("title")
	doc.route = form.get("route")
	doc.doc_type = form.get("document_type")
	doc.introduction_text = form.get("description")
	doc.button_label = form.get("submit_button_label") or "Submit"
	doc.success_message = form.get("success_message")
	doc.allowed_embedding_domains = form.get("allowed_embedding_domains")
	# CRM forms are served only by the CRM's own public page, so the native
	# `published` stays 0 (framework never renders /<route>); our own
	# `crm_published` flag drives whether the CRM page serves it publicly.
	doc.published = 0
	doc.crm_published = 1 if form.get("published") else 0
	# CRM forms are public, single-purpose lead/deal capture
	doc.login_required = 0
	doc.allow_multiple = 1
	doc.is_standard = 0
	doc.module = WEB_FORM_MODULE

	doc.set("web_form_fields", [])
	for i, f in enumerate(form.get("fields") or []):
		doc.append(
			"web_form_fields",
			{
				"fieldname": f.get("fieldname"),
				"label": f.get("label"),
				"fieldtype": f.get("fieldtype"),
				"options": f.get("options"),
				"reqd": 1 if f.get("reqd") else 0,
				"placeholder": f.get("placeholder"),
				"description": f.get("field_description"),
				"idx": i + 1,
			},
		)

	doc.save(ignore_permissions=True)
	return {"name": doc.name, "route": doc.route}


def _get_crm_web_form(name: str):
	doc = frappe.get_doc("Web Form", name)
	if doc.doc_type not in ALLOWED_DOCTYPES:
		frappe.throw(_("Not a CRM web form"))
	return doc


@frappe.whitelist()
def set_published(name: str, published: int) -> None:
	"""Publish/unpublish from the list, bypassing native Web Form role perms."""
	_check_manager()
	doc = _get_crm_web_form(name)
	doc.crm_published = 1 if int(published) else 0
	doc.published = 0
	doc.save(ignore_permissions=True)


@frappe.whitelist()
def delete_web_form(name: str) -> None:
	_check_manager()
	_get_crm_web_form(name)
	frappe.delete_doc("Web Form", name, ignore_permissions=True)


@frappe.whitelist()
def test_submit_web_form(name: str, values: dict | str) -> dict:
	"""Dry-run a submission for an author previewing a draft: validate required
	fields the same way the live form does, but create no record."""
	_check_manager()
	if isinstance(values, str):
		values = json.loads(values or "{}")

	doc = _get_crm_web_form(name)
	for f in doc.web_form_fields:
		if f.fieldtype in ("Section Break", "Column Break"):
			continue
		value = values.get(f.fieldname)
		if f.reqd and (value is None or value == ""):
			frappe.throw(_("{0} is required").format(f.label or f.fieldname))
	return {"test": True}


@frappe.whitelist(allow_guest=True)  # nosemgrep: frappe-semgrep-rules.rules.security.guest-whitelisted-method
def get_web_form(route: str) -> dict:
	"""Public config for a published CRM web form, for the espresso public page."""
	name = frappe.db.get_value(
		"Web Form", {"route": route, "crm_published": 1, "doc_type": ["in", ALLOWED_DOCTYPES]}
	)
	if not name:
		frappe.throw(_("Web form not found"), frappe.DoesNotExistError)

	doc = frappe.get_doc("Web Form", name)
	return {
		"name": doc.name,
		"title": doc.title,
		"description": doc.introduction_text,
		"route": doc.route,
		"document_type": doc.doc_type,
		"submit_button_label": doc.button_label or _("Submit"),
		"success_message": doc.success_message or _("Thank you!"),
		"fields": [
			{
				"fieldname": f.fieldname,
				"label": f.label,
				"fieldtype": f.fieldtype,
				"options": f.options,
				"reqd": f.reqd,
				"placeholder": f.placeholder,
				"description": f.description,
			}
			for f in doc.web_form_fields
		],
	}


def enrich_web_form_submission(doc, method=None):
	"""before_insert hook: when a Lead/Deal is created via ANY web form, apply the
	same enrichment the CRM applies on manual creation.

	The framework's Web Form `accept()` just inserts the target doc, so without this
	web submissions would miss Source / Organization / primary Contact. `accept()`
	sets `frappe.flags.in_web_form`, which is how we scope this to web submissions.
	"""
	if not frappe.flags.get("in_web_form"):
		return
	if doc.doctype not in ALLOWED_DOCTYPES:
		return

	# stamp the source so web-form records are identifiable/filterable
	if doc.meta.has_field("source") and not doc.get("source"):
		doc.source = ensure_web_form_source()

	if doc.doctype != "CRM Deal":
		return

	from crm.fcrm.doctype.crm_deal.crm_deal import create_contact, create_organization

	# auto-create the linked Organization from the org name (as the CRM does for deals)
	if doc.get("organization_name") and not doc.get("organization"):
		created = create_organization(doc)
		if created:
			doc.organization = created

	# auto-create & link a primary Contact from the person's details
	if not doc.get("contacts") and (
		doc.get("first_name") or doc.get("last_name") or doc.get("email") or doc.get("mobile_no")
	):
		contact = create_contact(doc)
		if contact:
			doc.append("contacts", {"contact": contact, "is_primary": 1})
