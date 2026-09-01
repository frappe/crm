import json

import frappe


def execute():
	if not frappe.db.exists("CRM Fields Layout", "CRM Task-Quick Entry"):
		return

	doc = frappe.get_doc("CRM Fields Layout", "CRM Task-Quick Entry")
	layout = json.loads(doc.layout or "[]")
	if not layout:
		return

	sections = _get_sections(layout)
	existing = {
		_fieldname(field)
		for section in sections
		for column in section.get("columns", [])
		for field in column.get("fields", [])
	}

	assignment_column = _find_column(sections, "assigned_to")
	if assignment_column:
		fields = assignment_column.setdefault("fields", [])
		if "assignment_type" not in existing:
			assigned_to_index = next(
				(index for index, field in enumerate(fields) if _fieldname(field) == "assigned_to"),
				0,
			)
			fields.insert(assigned_to_index, "assignment_type")
		if "assigned_role" not in existing:
			assigned_to_index = next(
				(index for index, field in enumerate(fields) if _fieldname(field) == "assigned_to"),
				len(fields) - 1,
			)
			fields.insert(assigned_to_index + 1, "assigned_role")

	if "checklist" not in existing:
		_append_section(
			layout,
			{
				"name": "checklist_section",
				"label": "Checklist",
				"columns": [{"name": "checklist_column", "fields": ["checklist"]}],
			}
		)

	progress_fields = {"completed_items", "total_items", "progress"}
	if not progress_fields.issubset(existing):
		missing = progress_fields - existing
		_append_section(
			layout,
			{
				"name": "progress_section",
				"label": "Progress",
				"hideBorder": True,
				"columns": [
					{
						"name": "progress_counts_column",
						"fields": [
							field for field in ["completed_items", "total_items"] if field in missing
						],
					},
					{
						"name": "progress_column",
						"fields": ["progress"] if "progress" in missing else [],
					},
				],
			}
		)

	doc.layout = json.dumps(layout)
	doc.save(ignore_permissions=True)


def _get_sections(layout):
	if any("sections" in item for item in layout):
		return [section for tab in layout for section in tab.get("sections", [])]
	return layout


def _append_section(layout, section):
	if any("sections" in item for item in layout):
		layout[-1].setdefault("sections", []).append(section)
	else:
		layout.append(section)


def _find_column(sections, fieldname):
	for section in sections:
		for column in section.get("columns", []):
			if any(_fieldname(field) == fieldname for field in column.get("fields", [])):
				return column
	return None


def _fieldname(field):
	return field.get("fieldname") if isinstance(field, dict) else field
