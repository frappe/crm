import json
from math import ceil

import frappe
from frappe.utils import random_string


def execute():
	layouts = frappe.get_all("CRM Fields Layout", fields=["name", "layout", "type"])

	for layout in layouts:
		old_layout = layout.layout
		new_layout = get_new_layout(old_layout, layout.type)

		frappe.db.set_value("CRM Fields Layout", layout.name, "layout", new_layout)


def get_new_layout(old_layout, type):
	if isinstance(old_layout, str):
		old_layout = json.loads(old_layout)
	new_layout = []
	already_converted = False

	starts_with_sections = False

	if not old_layout[0].get("sections"):
		starts_with_sections = True

	if starts_with_sections:
		old_layout = [{"sections": old_layout}]

	for tab in old_layout:
		new_tab = tab.copy()
		if "no_tabs" in new_tab:
			new_tab.pop("no_tabs")
		new_tab["sections"] = []
		new_tab["name"] = "tab_" + str(random_string(4))
		for section in tab.get("sections"):
			section["name"] = section.get("name") or "section_" + str(random_string(4))

			if section.get("label") == "Select Organization":
				section["name"] = "organization_section"
				section["hidden"] = 1
			elif section.get("label") == "Organization Details":
				section["name"] = "organization_details_section"
			elif section.get("label") == "Select Contact":
				section["name"] = "contact_section"
				section["hidden"] = 1
			elif section.get("label") == "Contact Details":
				section["name"] = "contact_details_section"

			if "contacts" in section:
				new_tab["sections"].append(section)
				continue
			if isinstance(section.get("columns"), list):
				already_converted = True
				break
			column_count = section.get("columns") or 3
			if type == "Side Panel":
				column_count = 1
			fields = section.get("fields") or []

			new_section = section.copy()

			if "fields" in new_section:
				new_section.pop("fields")
			new_section["columns"] = []

			if len(fields) == 0:
				new_section["columns"].append({"name": "column_" + str(random_string(4)), "fields": []})
				new_tab["sections"].append(new_section)
				continue

			if len(fields) == 1 and column_count > 1:
				new_section["columns"].append(
					{"name": "column_" + str(random_string(4)), "fields": [fields[0]]}
				)
				new_section["columns"].append({"name": "column_" + str(random_string(4)), "fields": []})
				new_tab["sections"].append(new_section)
				continue

			fields_per_column = ceil(len(fields) / column_count)
			for i in range(column_count):
				new_column = {
					"name": "column_" + str(random_string(4)),
					"fields": fields[i * fields_per_column : (i + 1) * fields_per_column],
				}
				new_section["columns"].append(new_column)
			new_tab["sections"].append(new_section)
		new_layout.append(new_tab)

	if starts_with_sections:
		new_layout = new_layout[0].get("sections")

	if already_converted:
		new_layout = old_layout

	if type == "Side Panel" and "sections" in new_layout[0]:
		new_layout = new_layout[0].get("sections")

	return json.dumps(new_layout)
