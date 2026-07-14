# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Hybrid forms API.

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
FORM_SOURCE = "Web Form"
FORM_MODULE = "FCRM"


def ensure_form_source() -> str:
	"""Return the 'Web Form' CRM Lead Source, creating it once if needed."""
	if not frappe.db.exists("CRM Lead Source", FORM_SOURCE):
		frappe.get_doc({"doctype": "CRM Lead Source", "source_name": FORM_SOURCE}).insert(
			ignore_permissions=True
		)
	return FORM_SOURCE


# Fieldtypes a form can render/collect — standard + custom fields of these types
# show up in the picker. Excludes types that need external data or special widgets
# (Link/Dynamic Link, Table, Attach, etc.), which can't be safely collected on a
# public form.
SUPPORTED_FIELDTYPES = (
	"Data",
	"Small Text",
	"Text",
	"Long Text",
	"Text Editor",
	"HTML Editor",
	"Markdown Editor",
	"Select",
	"Int",
	"Float",
	"Currency",
	"Percent",
	"Check",
	"Date",
	"Datetime",
	"Time",
	"Phone",
	"Color",
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

# Starting layout of a brand-new form, per target doctype: labelled sections,
# each a list of columns, each column a list of fieldnames. A sensible
# contact-capture starting point the author can then edit.
SEED_LAYOUT = {
	"CRM Lead": [
		{
			"label": "Personal Details",
			"columns": [["first_name", "email"], ["last_name", "phone"]],
		},
	],
	"CRM Deal": [
		{
			"label": "Personal Details",
			"columns": [["first_name", "email"], ["last_name", "phone"]],
		},
		{
			"label": "Organization Details",
			"columns": [["organization_name"]],
		},
	],
}


def _seeded_visible_fieldnames(document_type: str) -> set:
	names = set()
	for section in SEED_LAYOUT.get(document_type, []):
		for col in section["columns"]:
			names.update(col)
	return names


def _mappable_fields(document_type: str) -> list[dict]:
	"""Fields of a target DocType a form may collect (shared by the picker and by
	the brand-new-form seeding)."""
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
				"default": df.default,
			}
		)
	return fields


def _default_status(document_type: str) -> str | None:
	"""The status a new Lead/Deal defaults to — mirrors the doctype controllers so
	the hidden 'Status' field is pre-filled with the value the CRM would use."""
	status_dt = "CRM Lead Status" if document_type == "CRM Lead" else "CRM Deal Status"
	preferred = "New" if document_type == "CRM Lead" else "Qualification"
	if frappe.db.exists(status_dt, preferred):
		return preferred
	rows = frappe.get_all(status_dt, {"type": "Open"}, pluck="name")
	return rows[0] if rows else None


def _seed_visible_fields(document_type: str) -> list[dict]:
	"""Web-form rows for a new form's visible layout: the curated contact set,
	arranged into labelled sections and columns (with Section/Column breaks)."""
	catalog = {f["fieldname"]: f for f in _mappable_fields(document_type)}

	def _break(fieldtype, i, label=""):
		prefix = "section_break" if fieldtype == "Section Break" else "column_break"
		return {
			"fieldname": f"{prefix}_seed{i}",
			"label": label,
			"fieldtype": fieldtype,
			"options": "",
			"reqd": 0,
			"placeholder": "",
			"field_description": "",
		}

	rows = []
	n = 0
	for section in SEED_LAYOUT.get(document_type, []):
		n += 1
		rows.append(_break("Section Break", n, section.get("label") or ""))
		for ci, col in enumerate(section["columns"]):
			if ci > 0:
				n += 1
				rows.append(_break("Column Break", n))
			for fn in col:
				f = catalog.get(fn)
				if not f:
					continue
				rows.append(
					{
						"fieldname": f["fieldname"],
						"label": f["label"],
						"fieldtype": f["fieldtype"],
						"options": f["options"],
						"reqd": 1 if f["reqd"] else 0,
						"placeholder": "",
						"field_description": "",
					}
				)
	return rows


def _seed_hidden_fields(document_type: str) -> list[dict]:
	"""Mandatory fields a public visitor should not fill (e.g. Status, a Link the
	system sets). Seeded into the hidden section with a sensible default so the
	author sees them and can override the value applied on submission."""
	meta = frappe.get_meta(document_type)
	visible = _seeded_visible_fieldnames(document_type)
	hidden = []
	for df in meta.fields:
		if not df.reqd or df.fieldname in visible:
			continue
		if df.fieldtype in SUPPORTED_FIELDTYPES and df.fieldname not in DENIED_FIELDNAMES:
			continue  # a fillable mandatory field belongs in the visible layout
		default = _default_status(document_type) if df.fieldname == "status" else (df.default or "")
		hidden.append(
			{
				"fieldname": df.fieldname,
				"label": df.label or df.fieldname,
				"fieldtype": df.fieldtype,
				"options": df.options or "",
				"default": default,
			}
		)
	return hidden


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
		frappe.throw(_("Forms can only map to: {0}").format(", ".join(ALLOWED_DOCTYPES)))
	return _mappable_fields(document_type)


@frappe.whitelist()
def get_hidden_seed(document_type: str) -> list[dict]:
	"""The system-managed hidden required fields for a doctype (e.g. Status) with
	their default value. Used by the builder to reconcile on a doctype switch."""
	if document_type not in ALLOWED_DOCTYPES:
		frappe.throw(_("Forms can only map to: {0}").format(", ".join(ALLOWED_DOCTYPES)))
	return _seed_hidden_fields(document_type)


@frappe.whitelist()
def list_forms() -> list[dict]:
	"""CRM forms only (native Web Form records mapped to Lead/Deal)."""
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
def get_form_config(name: str) -> dict:
	"""Full config for the builder, read from the native Web Form record."""
	_check_manager()
	doc = frappe.get_doc("Web Form", name)
	if doc.doc_type not in ALLOWED_DOCTYPES:
		frappe.throw(_("Not a CRM form"))
	return {
		"name": doc.name,
		"title": doc.title,
		"route": doc.route,
		"document_type": doc.doc_type,
		"published": doc.crm_published,
		"submit_button_label": doc.button_label or _("Submit"),
		"description": doc.introduction_text or "",
		"success_message": doc.success_message or "",
		"redirect_url": doc.success_url or "",
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
		"hidden_fields": _load_hidden_fields(doc),
	}


def _load_hidden_fields(doc) -> list[dict]:
	try:
		return json.loads(doc.get("crm_hidden_defaults") or "[]")
	except Exception:
		return []


def _assert_hidden_defaults_set(hidden: list[dict]):
	"""Publishing requires every hidden required field to carry a default — a blank
	one would break record creation on submission. Drafts may save without them."""
	missing = [
		h.get("label") or h.get("fieldname") for h in hidden if not str(h.get("default") or "").strip()
	]
	if missing:
		frappe.throw(_("Set a default value before publishing for: {0}").format(", ".join(missing)))


@frappe.whitelist()
def save_form(name: str | None, form: dict | str) -> dict:
	"""Create/update a native Web Form scoped to CRM doctypes."""
	_check_manager()
	if isinstance(form, str):
		form = json.loads(form or "{}")

	if form.get("document_type") not in ALLOWED_DOCTYPES:
		frappe.throw(_("Forms can only map to: {0}").format(", ".join(ALLOWED_DOCTYPES)))

	doc = frappe.get_doc("Web Form", name) if name else frappe.new_doc("Web Form")
	if name and doc.doc_type not in ALLOWED_DOCTYPES:
		frappe.throw(_("Not a CRM form"))

	doc.title = form.get("title")
	doc.route = form.get("route")
	doc.doc_type = form.get("document_type")
	doc.introduction_text = form.get("description")
	doc.button_label = form.get("submit_button_label") or "Submit"
	doc.success_message = form.get("success_message")
	# redirect visitors here after a successful submission (native Web Form field);
	# blank falls back to showing the success message
	doc.success_url = form.get("redirect_url") or ""
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
	doc.module = FORM_MODULE

	# brand-new form → seed a starting contact-capture layout (only on create)
	fields = form.get("fields")
	if not name and not fields:
		fields = _seed_visible_fields(form["document_type"])

	# only rewrite the layout when fields were actually sent — an update that omits
	# `fields` (e.g. a settings-only save) must not wipe the existing layout
	if fields is not None:
		doc.set("web_form_fields", [])
		for i, f in enumerate(fields):
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

	# hidden required fields: mandatory fields kept out of the visible form, with
	# the default value applied on submission (see enrich_form_submission). Seeded
	# once on create (e.g. Status); thereafter whatever the builder sends wins.
	hidden = form.get("hidden_fields")
	if hidden is None and not name:
		hidden = _seed_hidden_fields(form["document_type"])
	if isinstance(hidden, str):
		hidden = json.loads(hidden or "[]")
	hidden = hidden or []
	if doc.crm_published:
		_assert_hidden_defaults_set(hidden)
	doc.crm_hidden_defaults = json.dumps(hidden) if hidden else ""

	doc.save(ignore_permissions=True)
	return {"name": doc.name, "route": doc.route}


def _get_crm_form(name: str):
	doc = frappe.get_doc("Web Form", name)
	if doc.doc_type not in ALLOWED_DOCTYPES:
		frappe.throw(_("Not a CRM form"))
	return doc


@frappe.whitelist()
def set_published(name: str, published: int) -> None:
	"""Publish/unpublish from the list, bypassing native Web Form role perms."""
	_check_manager()
	doc = _get_crm_form(name)
	if int(published):
		_assert_hidden_defaults_set(_load_hidden_fields(doc))
	doc.crm_published = 1 if int(published) else 0
	doc.published = 0
	doc.save(ignore_permissions=True)


@frappe.whitelist()
def delete_form(name: str) -> None:
	_check_manager()
	_get_crm_form(name)
	frappe.delete_doc("Web Form", name, ignore_permissions=True)


@frappe.whitelist()
def test_submit_form(name: str, values: dict | str) -> dict:
	"""Dry-run a submission for an author previewing a draft: validate required
	fields the same way the live form does, but create no record."""
	_check_manager()
	if isinstance(values, str):
		values = json.loads(values or "{}")

	doc = _get_crm_form(name)
	for f in doc.web_form_fields:
		if f.fieldtype in ("Section Break", "Column Break"):
			continue
		value = values.get(f.fieldname)
		if f.reqd and (value is None or value == ""):
			frappe.throw(_("{0} is required").format(f.label or f.fieldname))
	return {"test": True}


# Public form serving + submission run through the framework's own Web Form engine:
# the CRM page (`www/crm_form.py`) renders the published form and posts to the
# built-in `accept()`, which triggers `enrich_form_submission` below via the
# `in_web_form` flag. No CRM-owned guest endpoint is needed for that path.


def enrich_form_submission(doc):
	"""Called from the CRM Lead/Deal `before_insert`: when the record is created via a
	web form, apply the same enrichment the CRM applies on manual creation.

	The framework's Web Form `accept()` just inserts the target doc, so without this
	web submissions would miss Source / Organization / primary Contact. `accept()`
	sets `frappe.flags.in_web_form`, which is how we scope this to web submissions.
	"""
	if not frappe.flags.get("in_web_form"):
		return
	if doc.doctype not in ALLOWED_DOCTYPES:
		return

	_apply_hidden_defaults(doc)

	# stamp the source so form records are identifiable/filterable
	if doc.meta.has_field("source") and not doc.get("source"):
		doc.source = ensure_form_source()

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


def _apply_hidden_defaults(doc):
	"""Apply the submitting form's hidden-field defaults (e.g. Status) to fields the
	visitor didn't fill, so mandatory values are present before the record is saved."""
	web_form = frappe.form_dict.get("web_form")
	if not web_form:
		return
	# `web_form` comes from the (client-controllable) POST body — only trust a CRM
	# form that targets this exact doctype, else a submission could pull in another
	# form's defaults (or a different doctype's).
	form = frappe.db.get_value("Web Form", web_form, ["doc_type", "crm_hidden_defaults"], as_dict=True)
	if not form or form.doc_type not in ALLOWED_DOCTYPES or form.doc_type != doc.doctype:
		return
	raw = form.crm_hidden_defaults
	if not raw:
		return
	try:
		hidden = json.loads(raw)
	except Exception:
		return
	for h in hidden:
		fieldname = h.get("fieldname")
		default = h.get("default")
		if (
			fieldname
			and default not in (None, "")
			and doc.meta.has_field(fieldname)
			and not doc.get(fieldname)
		):
			doc.set(fieldname, default)
