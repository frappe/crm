import json

import frappe
from frappe.model import default_fields


def execute():
	for layout in frappe.get_all("CRM Fields Layout", fields=["name", "dt", "layout"]):
		if not layout.layout or not layout.dt or not frappe.db.exists("DocType", layout.dt):
			continue

		try:
			parsed = json.loads(layout.layout)
		except ValueError:
			continue

		if not isinstance(parsed, list):
			continue

		valid = {f.fieldname for f in frappe.get_meta(layout.dt).fields} | set(default_fields)
		if remove_stale_fieldnames(parsed, valid):
			frappe.db.set_value(
				"CRM Fields Layout", layout.name, "layout", json.dumps(parsed), update_modified=False
			)


def remove_stale_fieldnames(layout, valid):
	changed = False
	for item in layout:
		if not isinstance(item, dict):
			continue
		sections = item.get("sections") if "sections" in item else [item]
		for section in sections or []:
			for column in section.get("columns") or []:
				if not column or not column.get("fields"):
					continue
				kept = [f for f in column["fields"] if f in valid]
				if len(kept) != len(column["fields"]):
					column["fields"] = kept
					changed = True
	return changed
