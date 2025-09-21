import json
import frappe

def execute():
	if not frappe.db.exists("CRM Fields Layout", {"dt": "CRM Lead", "type": "Side Panel"}):
		create_doctype_fields_layout("CRM Lead")

	if not frappe.db.exists("CRM Fields Layout", {"dt": "CRM Deal", "type": "Side Panel"}):
		create_doctype_fields_layout("CRM Deal")

def create_doctype_fields_layout(doctype):
	not_allowed_fieldtypes = [
		"Section Break",
		"Column Break",
	]

	fields = frappe.get_meta(doctype).fields
	fields = [field for field in fields if field.fieldtype not in not_allowed_fieldtypes]

	sections = {}
	section_fields = []
	last_section = None

	for field in fields:
		if field.fieldtype == "Tab Break" and last_section:
			sections[last_section]["fields"] = section_fields
			last_section = None
			if field.read_only:
				section_fields = []
				continue
		if field.fieldtype == "Tab Break":
			if field.read_only:
				section_fields = []
				continue
			section_fields = []
			last_section = field.fieldname
			sections[field.fieldname] = {
				"label": field.label,
				"name": field.fieldname,
				"opened": True,
				"fields": [],
			}
			if field.fieldname == "contacts_tab":
				sections[field.fieldname]["editable"] = False
				sections[field.fieldname]["contacts"] = []
		else:
			section_fields.append(field.fieldname)

	section_fields = []
	for section in sections:
		if section == "contacts_tab":
			sections[section]["name"] = "contacts_section"
			sections[section].pop("fields", None)
		section_fields.append(sections[section])

	frappe.get_doc({
		"doctype": "CRM Fields Layout",
		"dt": doctype,
		"type": "Side Panel",
		"layout": json.dumps(section_fields),
	}).insert(ignore_permissions=True)

	return section_fields