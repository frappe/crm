# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import copy

from frappe.desk.doctype.form_layout.app_layout import read_app_layout
from frappe.desk.doctype.form_layout.form_layout import (
	data_fieldnames,
	free_name,
	inline_fields,
	name_layout_containers,
	parse_layout,
	wrap_tabless,
)

V1_ONLY_KEYS = ("editable", "contacts", "editingLabel", "hidden")
SIDE_PANEL_RUNTIME_SECTIONS = ("lost_reason_section", "contacts_section")
DEAL_QUICK_ENTRY_LINK_SECTIONS = ("organization_section", "contact_section")
DEAL_QUICK_ENTRY_DROPPED_SECTIONS = ("organization_details_section", "contact_details_section")
STATUS_DOCTYPES = ("CRM Lead", "CRM Deal")


def convert_layout(dt: str, v1_type: str, tree: list) -> list:
	"""A `CRM Fields Layout` tree as the Form Layout tree desk v2 reads; always tabbed, always valid."""
	return LayoutConversion(dt, v1_type).convert(tree)


class LayoutConversion:
	def __init__(self, dt: str, v1_type: str):
		self.dt = dt
		self.v1_type = v1_type

	def convert(self, tree: list) -> list:
		tabs = wrap_tabless(copy.deepcopy(tree))
		for tab in tabs:
			tab["sections"] = [section for section in as_list(tab.get("sections")) if self.keeps(section)]
		if self.dt in STATUS_DOCTYPES and self.v1_type == "Side Panel":
			tabs[0]["sections"][:0] = [sla_section(), lost_reason_section()]
		for tab in tabs:
			strip_tab(tab)
		if self.v1_type == "Quick Entry":
			use_app_inline_fields(tabs, self.dt)
		name_layout_containers(tabs)
		rename_clashes(tabs, data_fieldnames(self.dt))
		return tabs

	def keeps(self, section) -> bool:
		if not isinstance(section, dict):
			return False
		name = section.get("name")
		if self.v1_type == "Side Panel" and name in SIDE_PANEL_RUNTIME_SECTIONS:
			return False
		if self.dt == "CRM Deal" and self.v1_type == "Quick Entry":
			if name in DEAL_QUICK_ENTRY_DROPPED_SECTIONS:
				return False
			if name in DEAL_QUICK_ENTRY_LINK_SECTIONS:
				return True
		return not section.get("hidden")


def sla_section() -> dict:
	return {
		"name": "sla_section",
		"label": "SLA",
		"opened": True,
		"dependsOn": "sla",
		"columns": [{"name": "sla_column", "fields": ["sla_status", "communication_status"]}],
	}


def lost_reason_section() -> dict:
	return {
		"name": "lost_reason_section",
		"label": "Lost Reason",
		"opened": True,
		"dependsOn": "lost_reason",
		"columns": [{"name": "lost_reason_column", "fields": ["lost_reason", "lost_notes"]}],
	}


def use_app_inline_fields(tabs: list, dt: str):
	"""Define a field inline where the doctype's own Quick Entry file does, as Contact's read-only `email_id`."""
	app_layout = read_app_layout(dt, "Quick Entry")
	if not app_layout:
		return
	definitions = {field["fieldname"]: field for field in inline_fields(parse_layout(app_layout.layout))}
	placed = set()
	for tab in tabs:
		for section in tab["sections"]:
			for column in section["columns"]:
				column["fields"] = inline_column(column["fields"], definitions, placed)


def inline_column(fields: list, definitions: dict, placed: set) -> list:
	# Form Layout refuses an inline field placed twice, so a repeat drops.
	kept = []
	for name in fields:
		if name not in definitions:
			kept.append(name)
		elif name not in placed:
			placed.add(name)
			kept.append(copy.deepcopy(definitions[name]))
	return kept


def strip_tab(tab: dict):
	strip_keys(tab)
	for section in tab["sections"]:
		strip_keys(section)
		section["columns"] = [
			column for column in as_list(section.get("columns")) if isinstance(column, dict)
		]
		for column in section["columns"]:
			strip_keys(column)
			names = (fieldname_of(field) for field in as_list(column.get("fields")))
			column["fields"] = [name for name in names if name]


def strip_keys(node: dict):
	for key in V1_ONLY_KEYS:
		node.pop(key, None)


def as_list(value) -> list:
	return value if isinstance(value, list) else []


def fieldname_of(field) -> str | None:
	# Form Layout reads a dict as a field the layout defines itself, and refuses a real one.
	if isinstance(field, dict):
		field = field.get("fieldname")
	return field if isinstance(field, str) and field else None


def rename_clashes(tabs: list, fieldnames: set[str]):
	"""Rename a name Form Layout would refuse, so a migrate never fails on a v1 layout."""
	rename_in_group(tabs, set(fieldnames))
	sections = [section for tab in tabs for section in tab["sections"]]
	rename_in_group(sections, set(fieldnames))
	for section in sections:
		rename_in_group(section["columns"], set())


def rename_in_group(nodes: list, taken: set[str]):
	for node in nodes:
		if node["name"] in taken:
			node["name"] = free_name(node["name"], taken)
		taken.add(node["name"])
