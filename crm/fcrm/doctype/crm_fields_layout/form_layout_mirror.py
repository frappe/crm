# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe

from crm.fcrm.doctype.crm_fields_layout.form_layout_conversion import convert_layout

# Until the cutover, v1 owns each (dt, type)'s default Form Layout row; a desk v2 edit to it is lost.
FORM_LAYOUT_TYPES = {"Quick Entry": "Quick Entry", "Side Panel": "Side Panel", "Data Fields": "Details"}
MIRRORED_DOCTYPES = (
	"CRM Lead",
	"CRM Deal",
	"CRM Organization",
	"CRM Task",
	"FCRM Note",
	"CRM Call Log",
)


def mirror_layout(doc):
	"""Write the default Form Layout row of a `CRM Fields Layout` row, or delete it when v1's is empty."""
	previous = doc.get_doc_before_save()
	if previous and (previous.dt, previous.type) != (doc.dt, doc.type):
		remove_mirrored_layout(previous)
	if not is_mirrored(doc):
		return
	tree = read_tree(doc.layout)
	if tree is None:
		return
	if not tree:
		remove_mirrored_layout(doc)
		return
	write_default_row(doc.dt, FORM_LAYOUT_TYPES[doc.type], convert_layout(doc.dt, doc.type, tree))


def remove_mirrored_layout(doc):
	if not is_mirrored(doc):
		return
	name = default_row_name(doc.dt, FORM_LAYOUT_TYPES[doc.type])
	if name:
		frappe.delete_doc("Form Layout", name, ignore_permissions=True)


def mirror_all_layouts():
	for name in frappe.get_all(
		"CRM Fields Layout",
		filters={"dt": ("in", MIRRORED_DOCTYPES), "type": ("in", list(FORM_LAYOUT_TYPES))},
		pluck="name",
	):
		mirror_layout(frappe.get_doc("CRM Fields Layout", name))


def is_mirrored(doc) -> bool:
	return doc.dt in MIRRORED_DOCTYPES and doc.type in FORM_LAYOUT_TYPES


def write_default_row(dt: str, type: str, layout: list):
	name = default_row_name(dt, type)
	row = frappe.get_doc("Form Layout", name) if name else frappe.new_doc("Form Layout", dt=dt, type=type)
	# A skipped save keeps a lost deal's v1 rewrite from writing Form Layout again.
	if name and read_tree(row.layout) == layout:
		return
	row.layout = frappe.as_json(layout)
	row.save(ignore_permissions=True)


def default_row_name(dt: str, type: str) -> str | None:
	rows = frappe.get_all(
		"Form Layout",
		filters={"dt": dt, "type": type, "condition": ("is", "not set")},
		pluck="name",
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
