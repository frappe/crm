# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit

from crm.fcrm.doctype.crm_web_form.crm_web_form import ALLOWED_DOCTYPES

WEB_FORM_SOURCE = "Web Form"


def ensure_web_form_source() -> str:
	"""Return the 'Web Form' CRM Lead Source, creating it once if needed."""
	if not frappe.db.exists("CRM Lead Source", WEB_FORM_SOURCE):
		frappe.get_doc(
			{"doctype": "CRM Lead Source", "source_name": WEB_FORM_SOURCE}
		).insert(ignore_permissions=True)
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


@frappe.whitelist(allow_guest=True)
def get_web_form(route: str) -> dict:
	"""Public config for a published web form. Raises 404 if not published."""
	name = frappe.db.get_value("CRM Web Form", {"route": route, "published": 1})
	if not name:
		frappe.throw(_("Web form not found"), frappe.DoesNotExistError)

	doc = frappe.get_doc("CRM Web Form", name)
	return {
		"title": doc.title,
		"description": doc.description,
		"route": doc.route,
		"document_type": doc.document_type,
		"submit_button_label": doc.submit_button_label or _("Submit"),
		"success_message": doc.success_message or _("Thank you!"),
		"fields": [
			{
				"fieldname": f.fieldname,
				"label": f.label,
				"fieldtype": f.fieldtype,
				"options": f.options,
				"reqd": f.reqd,
				"placeholder": f.placeholder,
				"description": f.field_description,
			}
			for f in doc.fields
		],
	}


@frappe.whitelist()
def save_web_form(name: str, form: dict | str) -> dict:
	"""Persist builder changes: scalar settings + the full field list (rebuilt)."""
	if isinstance(form, str):
		form = json.loads(form or "{}")

	doc = frappe.get_doc("CRM Web Form", name)
	for key in (
		"title",
		"route",
		"document_type",
		"description",
		"submit_button_label",
		"success_message",
		"allowed_embedding_domains",
	):
		if key in form:
			doc.set(key, form[key])
	doc.published = 1 if form.get("published") else 0

	doc.set("fields", [])
	for i, f in enumerate(form.get("fields") or []):
		doc.append(
			"fields",
			{
				"fieldname": f.get("fieldname"),
				"label": f.get("label"),
				"fieldtype": f.get("fieldtype"),
				"options": f.get("options"),
				"reqd": 1 if f.get("reqd") else 0,
				"placeholder": f.get("placeholder"),
				"field_description": f.get("field_description"),
				"idx": i + 1,
			},
		)

	doc.save()
	frappe.db.commit()
	return {
		"name": doc.name,
		"route": doc.route,
		"fields": [{"name": x.name, "fieldname": x.fieldname} for x in doc.fields],
	}


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(key="route", limit=20, seconds=60 * 60)
def submit_web_form(route: str, values: dict | str) -> dict:
	"""Create a record of the form's target DocType from a public submission.

	Runs as Guest, so it only ever writes the fields declared on the form and
	only into the allow-listed DocTypes.
	"""
	if isinstance(values, str):
		values = json.loads(values or "{}")
	if not isinstance(values, dict):
		frappe.throw(_("Invalid submission"))

	name = frappe.db.get_value("CRM Web Form", {"route": route, "published": 1})
	# allow logged-in authors to test-submit an unpublished (draft) form
	if not name and frappe.session.user != "Guest" and frappe.has_permission("CRM Web Form", "read"):
		name = frappe.db.get_value("CRM Web Form", {"route": route})
	if not name:
		frappe.throw(_("Web form not found"), frappe.DoesNotExistError)

	form = frappe.get_doc("CRM Web Form", name)
	if form.document_type not in ALLOWED_DOCTYPES:
		frappe.throw(_("This form cannot accept submissions"))

	doc = frappe.new_doc(form.document_type)
	for f in form.fields:
		if f.fieldtype in ("Section Break", "Column Break"):
			continue
		value = values.get(f.fieldname)
		if f.reqd and (value is None or value == ""):
			frappe.throw(_("{0} is required").format(f.label or f.fieldname))
		if value is not None and value != "":
			doc.set(f.fieldname, value)

	# A draft form is only reachable by an author previewing it, so treat submissions
	# as a dry run: validate everything above, but don't create a real record.
	if not form.published:
		return {
			"name": None,
			"document_type": form.document_type,
			"success_message": form.success_message or _("Thank you!"),
			"test": True,
		}

	# auto-create the linked Organization from the org name (as the CRM does for deals)
	org_field = doc.meta.get_field("organization")
	if (
		org_field
		and org_field.fieldtype == "Link"
		and org_field.options == "CRM Organization"
		and doc.get("organization_name")
		and not doc.get("organization")
	):
		from crm.fcrm.doctype.crm_deal.crm_deal import create_organization

		created = create_organization(doc)
		if created:
			doc.organization = created

	# for deals, auto-create & link a primary Contact from the person's details (as the CRM does)
	if (
		form.document_type == "CRM Deal"
		and not doc.get("contacts")
		and (doc.get("first_name") or doc.get("last_name") or doc.get("email") or doc.get("mobile_no"))
	):
		from crm.fcrm.doctype.crm_deal.crm_deal import create_contact

		contact = create_contact(doc)
		if contact:
			doc.append("contacts", {"contact": contact, "is_primary": 1})

	# stamp the source so web-form records are identifiable/filterable
	if doc.meta.has_field("source") and not doc.get("source"):
		doc.source = ensure_web_form_source()

	doc.insert(ignore_permissions=True)
	frappe.db.commit()

	return {
		"name": doc.name,
		"document_type": form.document_type,
		"success_message": form.success_message or _("Thank you!"),
		"test": False,
	}
