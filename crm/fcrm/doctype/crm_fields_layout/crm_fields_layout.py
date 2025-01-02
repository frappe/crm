# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import random_string


class CRMFieldsLayout(Document):
	pass


@frappe.whitelist()
def get_fields_layout(doctype: str, type: str):
	tabs = []
	layout = None

	if frappe.db.exists("CRM Fields Layout", {"dt": doctype, "type": type}):
		layout = frappe.get_doc("CRM Fields Layout", {"dt": doctype, "type": type})

	if layout and layout.layout:
		tabs = json.loads(layout.layout)

	if not tabs:
		tabs = get_default_layout(doctype)

	has_tabs = tabs[0].get("sections") if tabs and tabs[0] else False

	if not has_tabs:
		tabs = [{"name": "first_tab", "sections": tabs}]

	allowed_fields = []
	for tab in tabs:
		for section in tab.get("sections"):
			if "columns" not in section:
				continue
			for column in section.get("columns"):
				if not column.get("fields"):
					continue
				allowed_fields.extend(column.get("fields"))

	fields = frappe.get_meta(doctype).fields
	fields = [field for field in fields if field.fieldname in allowed_fields]

	for tab in tabs:
		for section in tab.get("sections"):
			for column in section.get("columns") if section.get("columns") else []:
				for field in column.get("fields") if column.get("fields") else []:
					field = next((f for f in fields if f.fieldname == field), None)
					if field:
						field = field.as_dict()
						column["fields"][column.get("fields").index(field["fieldname"])] = field

	return tabs or []


@frappe.whitelist()
def save_fields_layout(doctype: str, type: str, layout: str):
	if frappe.db.exists("CRM Fields Layout", {"dt": doctype, "type": type}):
		doc = frappe.get_doc("CRM Fields Layout", {"dt": doctype, "type": type})
	else:
		doc = frappe.new_doc("CRM Fields Layout")

	doc.update(
		{
			"dt": doctype,
			"type": type,
			"layout": layout,
		}
	)
	doc.save(ignore_permissions=True)

	return doc.layout


def get_default_layout(doctype: str):
	fields = frappe.get_meta(doctype).fields

	tabs = []

	if fields and fields[0].fieldtype != "Tab Break":
		sections = []
		if fields and fields[0].fieldtype != "Section Break":
			sections.append(
				{
					"name": "section_" + str(random_string(4)),
					"columns": [{"name": "column_" + str(random_string(4)), "fields": []}],
				}
			)
		tabs.append({"name": "tab_" + str(random_string(4)), "sections": sections})

	for field in fields:
		if field.fieldtype == "Tab Break":
			tabs.append(
				{
					"name": "tab_" + str(random_string(4)),
					"sections": [
						{
							"name": "section_" + str(random_string(4)),
							"columns": [{"name": "column_" + str(random_string(4)), "fields": []}],
						}
					],
				}
			)
		elif field.fieldtype == "Section Break":
			tabs[-1]["sections"].append(
				{
					"name": "section_" + str(random_string(4)),
					"columns": [{"name": "column_" + str(random_string(4)), "fields": []}],
				}
			)
		elif field.fieldtype == "Column Break":
			tabs[-1]["sections"][-1]["columns"].append(
				{"name": "column_" + str(random_string(4)), "fields": []}
			)
		else:
			tabs[-1]["sections"][-1]["columns"][-1]["fields"].append(field.fieldname)

	return tabs
