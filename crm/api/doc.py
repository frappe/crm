import frappe
from frappe.model.document import get_controller
from frappe.model import no_value_fields
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
def get_list_data(doctype: str, filters: dict, order_by: str):
	columns = [
		{"label": "Name", "type": "Data", "key": "name", "width": "16rem"},
		{"label": "Last Modified", "type": "Datetime", "key": "modified", "width": "8rem"},
	]
	rows = ["name"]

	is_default = True

	if frappe.db.exists("CRM List View Settings", doctype):
		list_view_settings = frappe.get_doc("CRM List View Settings", doctype)
		columns = frappe.parse_json(list_view_settings.columns)
		rows = frappe.parse_json(list_view_settings.rows)
		is_default = False
	else:
		list = get_controller(doctype)

		if hasattr(list, "default_list_data"):
			columns = list.default_list_data().get("columns")
			rows = list.default_list_data().get("rows")

	# check if rows has all keys from columns if not add them
	for column in columns:
		if column.get("key") not in rows:
			rows.append(column.get("key"))

	data = frappe.get_all(
		doctype,
		fields=rows,
		filters=filters,
		order_by=order_by,
		page_length=20,
	) or []

	fields = frappe.get_meta(doctype).fields
	fields = [field for field in fields if field.fieldtype not in no_value_fields]
	fields = [
		{
			"label": field.label,
			"type": field.fieldtype,
			"value": field.fieldname,
			"options": field.options,
		}
		for field in fields
		if field.label and field.fieldname
	]

	std_fields = [
		{"label": "Name", "type": "Data", "value": "name"},
		{"label": "Created On", "type": "Datetime", "value": "creation"},
		{"label": "Last Modified", "type": "Datetime", "value": "modified"},
		{
			"label": "Modified By",
			"type": "Link",
			"value": "modified_by",
			"options": "User",
		},
		{"label": "Owner", "type": "Link", "value": "owner", "options": "User"},
	]

	for field in std_fields:
		if field.get('value') not in rows:
			rows.append(field.get('value'))
		if field not in fields:
			fields.append(field)

	return {
		"data": data,
		"columns": columns,
		"rows": rows,
		"fields": fields,
		"is_default": is_default,
	}


@frappe.whitelist()
def get_doctype_fields(doctype):
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
				"opened": True,
				"fields": [],
			}
		else:
			section_fields.append(get_field_obj(field))

	all_fields = []
	for section in sections:
		all_fields.append(sections[section])

	return all_fields


def get_field_obj(field):
	obj = {
		"label": field.label,
		"type": get_type(field),
		"name": field.fieldname,
	}

	obj["placeholder"] = "Add " + field.label + "..."

	if field.fieldtype == "Link":
		obj["placeholder"] = "Select " + field.label + "..."
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
	elif field.fieldtype == "Check":
		return "checkbox"
	elif field.fieldtype == "Int":
		return "number"
	elif field.fieldtype in ["Small Text", "Text", "Long Text"]:
		return "textarea"
	elif field.read_only:
		return "read_only"
	return field.fieldtype.lower()
