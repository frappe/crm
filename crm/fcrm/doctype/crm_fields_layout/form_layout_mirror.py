# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.desk.doctype.form_layout.form_layout import default_filters

from crm.fcrm.doctype.crm_fields_layout.form_layout_conversion import convert_layout

FORM_LAYOUT_TYPES = {"Quick Entry": "Quick Entry", "Side Panel": "Side Panel", "Data Fields": "Details"}
MIRRORED_DOCTYPES = (
	"CRM Lead",
	"CRM Deal",
	"CRM Organization",
	"CRM Task",
	"FCRM Note",
	"CRM Call Log",
)
# CRM's layouts on doctypes it does not own name the app, so `/apps/desk` keeps frappe's.
FOREIGN_LAYOUTS = (("Contact", "Quick Entry"), ("Contact", "Side Panel"), ("Address", "Quick Entry"))
FOREIGN_LAYOUT_APP = "crm"
FOREIGN_DOCTYPES = ("Contact", "Address")


def mirror_layout(doc):
	"""Write the default Form Layout row of a `CRM Fields Layout` row, or delete it when nothing converts.

	Until the cutover v1 owns that row, so a desk v2 edit to it is lost at the next v1 save.
	"""
	previous = doc.get_doc_before_save()
	if previous and (previous.dt, previous.type) != (doc.dt, doc.type):
		remove_mirrored_layout(previous)
	if not is_mirrored(doc):
		return
	tree = read_tree(doc.layout)
	if tree is None:
		return
	layout = convert_layout(doc.dt, doc.type, tree)
	if not any(tab["sections"] for tab in layout):
		remove_mirrored_layout(doc)
		return
	write_default_row(doc.dt, FORM_LAYOUT_TYPES[doc.type], layout)


def remove_mirrored_layout(doc):
	if not is_mirrored(doc):
		return
	row = default_row(doc.dt, FORM_LAYOUT_TYPES[doc.type])
	if row:
		frappe.delete_doc("Form Layout", row.name, ignore_permissions=True)


def mirror_all_layouts(doctypes: tuple[str, ...] = MIRRORED_DOCTYPES + FOREIGN_DOCTYPES):
	for name in frappe.get_all(
		"CRM Fields Layout",
		filters={"dt": ("in", doctypes), "type": ("in", list(FORM_LAYOUT_TYPES))},
		pluck="name",
	):
		mirror_layout(frappe.get_doc("CRM Fields Layout", name))


def is_mirrored(doc) -> bool:
	if (doc.dt, doc.type) in FOREIGN_LAYOUTS:
		return True
	return doc.dt in MIRRORED_DOCTYPES and doc.type in FORM_LAYOUT_TYPES


def layout_app(dt: str) -> str | None:
	return None if dt in MIRRORED_DOCTYPES else FOREIGN_LAYOUT_APP


def write_default_row(dt: str, type: str, layout: list):
	stored = default_row(dt, type)
	# A skipped save keeps a lost deal's v1 rewrite from writing Form Layout again.
	if stored and not stored.omitted and read_tree(stored.layout) == layout:
		return
	row = (
		frappe.get_doc("Form Layout", stored.name)
		if stored
		else frappe.new_doc("Form Layout", dt=dt, type=type, app=layout_app(dt))
	)
	row.layout = frappe.as_json(layout)
	row.omitted = None
	row.save(ignore_permissions=True)


def default_row(dt: str, type: str):
	"""The oldest row with no condition in the mirror's app scope, the one desk v2 reads first."""
	rows = frappe.get_all(
		"Form Layout",
		filters=default_filters(dt, type, layout_app(dt)),
		fields=["name", "layout", "omitted"],
		order_by="creation asc",
		limit=1,
	)
	return rows[0] if rows else None


def read_tree(layout: str | None) -> list | None:
	"""The stored tree, `[]` when empty, or `None` when it is not a list v1 could read either."""
	try:
		tree = json.loads(layout) if layout else []
	except (json.JSONDecodeError, TypeError):
		return None
	return tree if isinstance(tree, list) else None
