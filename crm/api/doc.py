import frappe
from frappe.model.document import get_controller
from pypika import Criterion


@frappe.whitelist()
def sort_options(doctype: str):
	c = get_controller(doctype)

	if not hasattr(c, "sort_options"):
		return []

	return c.sort_options()

@frappe.whitelist()
def get_filterable_fields(doctype: str):
	DocField = frappe.qb.DocType("DocField")
	allowed_fieldtypes = [
		"Check",
		"Data",
		"Float",
		"Int",
		"Link",
		"Long Text",
		"Select",
		"Small Text",
		"Text Editor",
		"Text",
	]

	from_doc_fields = (
		frappe.qb.from_(DocField)
		.select(
			DocField.fieldname,
			DocField.fieldtype,
			DocField.label,
			DocField.name,
			DocField.options,
		)
		.where(DocField.parent == doctype)
		.where(DocField.hidden == False)
		.where(Criterion.any([DocField.fieldtype == i for i in allowed_fieldtypes]))
		.run(as_dict=True)
	)
	res = []
	res.extend(from_doc_fields)
	return res

@frappe.whitelist()
def get_doctype_fields(doctype):
	DocField = frappe.qb.DocType("DocField")
	CustomField = frappe.qb.DocType("Custom Field")
	not_allowed_fieldtypes = [
		"Section Break",
		"Column Break",
	]

	fields = (
		frappe.qb.from_(DocField)
		.select(
			DocField.fieldname,
			DocField.fieldtype,
			DocField.label,
			DocField.name,
			DocField.options,
			DocField.read_only,
			DocField.idx,
		)
		.where(DocField.parent == doctype)
		.where(DocField.hidden == False)
		.where(Criterion.notin(DocField.fieldtype, not_allowed_fieldtypes))
		.orderby(DocField.idx)
		.run(as_dict=True)
	)

	custom_fields = (
		frappe.qb.from_(CustomField)
		.select(
			CustomField.fieldname,
			CustomField.fieldtype,
			CustomField.label,
			CustomField.name,
			CustomField.options,
			CustomField.read_only,
			CustomField.idx,
			CustomField.insert_after,
		)
		.where(CustomField.dt == doctype)
		.where(CustomField.hidden == False)
		.where(Criterion.notin(CustomField.fieldtype, not_allowed_fieldtypes))
		.orderby(CustomField.idx)
		.run(as_dict=True)
	)

	all_fields = []
	all_fields.extend(fields)

	# Add custom fields based on insert_after
	for custom_field in custom_fields:
		if custom_field.insert_after:
			for i, field in enumerate(all_fields):
				if field.fieldname == custom_field.insert_after:
					all_fields.insert(i + 1, custom_field)
					break
		else:
			all_fields.prepend(custom_field)

	sections = {}
	section_fields = []
	last_section = None

	for field in all_fields:
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
				"opened": True,
				"fields": [],
			}
		else:
			section_fields.append(get_field_obj(field))

	deal_fields = []
	for section in sections:
		deal_fields.append(sections[section])

	return deal_fields

def get_field_obj(field):
	obj = {
		"label": field.label,
		"type": get_type(field),
		"name": field.fieldname,
	}

	obj["placeholder"] = "Add " + field.label.lower() + "..."

	if field.fieldtype == "Link":
		obj["placeholder"] = "Select " + field.label.lower() + "..."
		obj["doctype"] = field.options
	elif field.fieldtype == "Select":
		obj["options"] = [{"label": option, "value": option} for option in field.options.split("\n")]

	if field.read_only:
		obj["tooltip"] = "This field is read only and cannot be edited."

	return obj

def get_type(field):
	if field.fieldtype == "Data" and field.options == "Phone":
		return "phone"
	elif field.fieldtype == "Data" and field.options == "Email":
		return "email"
	elif field.read_only:
		return "read_only"
	return field.fieldtype.lower()