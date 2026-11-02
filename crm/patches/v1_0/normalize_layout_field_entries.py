"""Replace field dicts in saved layouts with fieldnames.

The Deal Quick Entry layout seeded in June 2024 mixed fieldnames with dicts like
``{"label": ..., "name": ..., "type": ...}``, and later patches carried them over.
Code reading layouts expects strings and raises TypeError on these dicts.
"""

import json

import frappe


def execute():
	for layout in frappe.get_all("CRM Fields Layout", fields=["name", "layout"]):
		try:
			parsed = json.loads(layout.layout or "[]")
		except ValueError:
			continue

		if isinstance(parsed, list) and normalize_field_entries(parsed):
			frappe.db.set_value("CRM Fields Layout", layout.name, "layout", json.dumps(parsed))


def normalize_field_entries(layout):
	changed = False
	for column in _iter_columns(layout):
		fields = column.get("fields") or []
		if any(isinstance(field, dict) for field in fields):
			column["fields"] = [fieldname for field in fields if (fieldname := _get_fieldname(field))]
			changed = True
	return changed


def _iter_columns(layout):
	for item in layout:
		for section in item.get("sections") or [item]:
			yield from (column for column in section.get("columns") or [] if column)


def _get_fieldname(field):
	return (field.get("fieldname") or field.get("name")) if isinstance(field, dict) else field
