# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.model.document import Document


class CRMFieldsLayout(Document):
	pass


@frappe.whitelist()
def get_fields_layout(doctype: str, type: str):
	tabs = []
	if frappe.db.exists("CRM Fields Layout", {"dt": doctype, "type": type}):
		layout = frappe.get_doc("CRM Fields Layout", {"dt": doctype, "type": type})
	else:
		return []

	if layout.layout:
		tabs = json.loads(layout.layout)

	has_tabs = tabs[0].get("sections") if tabs and tabs[0] else False

	if not has_tabs:
		tabs = [{"no_tabs": True, "sections": tabs}]

	allowed_fields = []
	for tab in tabs:
		for section in tab.get("sections"):
			if not section.get("fields"):
				continue
			allowed_fields.extend(section.get("fields"))

	fields = frappe.get_meta(doctype).fields
	fields = [field for field in fields if field.fieldname in allowed_fields]

	for tab in tabs:
		for section in tab.get("sections"):
			for field in section.get("fields") if section.get("fields") else []:
				field_meta = next((f for f in fields if f.fieldname == field), None)
				if field_meta:
					field_data = {
						"label": _(field_meta.label),
						"name": field_meta.fieldname,
						"type": field_meta.fieldtype,
						"fieldtype": field_meta.fieldtype,
						"mandatory": field_meta.reqd,
						"placeholder": field_meta.get("placeholder"),
						"filters": field_meta.get("link_filters"),
					}
					
					if field_meta.fieldtype == "Select" and field_meta.options:
						options = field_meta.options.split("\n")
						field_data["options"] = [{"label": _(option), "value": option} for option in options]
						field_data["options"].insert(0, {"label": "", "value": ""})
					else:
						field_data["options"] = field_meta.options

					section["fields"][section.get("fields").index(field)] = field_data

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
