import frappe
from frappe.model.document import get_controller
from frappe.model import no_value_fields
from pypika import Criterion

from crm.api.views import get_views


@frappe.whitelist()
def sort_options(doctype: str):
	fields = frappe.get_meta(doctype).fields
	fields = [field for field in fields if field.fieldtype not in no_value_fields]
	fields = [
		{
			"label": field.label,
			"value": field.fieldname,
		}
		for field in fields
		if field.label and field.fieldname
	]

	standard_fields = [
		{"label": "Name", "value": "name"},
		{"label": "Created On", "value": "creation"},
		{"label": "Last Modified", "value": "modified"},
		{"label": "Modified By", "value": "modified_by"},
		{"label": "Owner", "value": "owner"},
	]

	for field in standard_fields:
		fields.append(field)

	return fields


@frappe.whitelist()
def get_filterable_fields(doctype: str):
	allowed_fieldtypes = [
		"Check",
		"Data",
		"Float",
		"Int",
		"Currency",
		"Link",
		"Long Text",
		"Select",
		"Small Text",
		"Text Editor",
		"Text",
		"Duration",
		"Date",
		"Datetime",
	]

	c = get_controller(doctype)
	restricted_fields = []
	if hasattr(c, "get_non_filterable_fields"):
		restricted_fields = c.get_non_filterable_fields()

	res = []

	# append DocFields
	DocField = frappe.qb.DocType("DocField")
	doc_fields = get_fields_meta(DocField, doctype, allowed_fieldtypes, restricted_fields)
	res.extend(doc_fields)

	# append Custom Fields
	CustomField = frappe.qb.DocType("Custom Field")
	custom_fields = get_fields_meta(CustomField, doctype, allowed_fieldtypes, restricted_fields)
	res.extend(custom_fields)

	# append standard fields (getting error when using frappe.model.std_fields)
	standard_fields = [
		{"fieldname": "name", "fieldtype": "Link", "label": "ID", "options": doctype},
		{
			"fieldname": "owner",
			"fieldtype": "Link",
			"label": "Created By",
			"options": "User"
		},
		{
			"fieldname": "modified_by",
			"fieldtype": "Link",
			"label": "Last Updated By",
			"options": "User",
		},
		{"fieldname": "_user_tags", "fieldtype": "Data", "label": "Tags"},
		{"fieldname": "_liked_by", "fieldtype": "Data", "label": "Liked By"},
		{"fieldname": "_comments", "fieldtype": "Text", "label": "Comments"},
		{"fieldname": "_assign", "fieldtype": "Text", "label": "Assigned To"},
		{"fieldname": "creation", "fieldtype": "Datetime", "label": "Created On"},
		{"fieldname": "modified", "fieldtype": "Datetime", "label": "Last Updated On"},
	]
	for field in standard_fields:
		if (
			field.get("fieldname") not in restricted_fields and
			field.get("fieldtype") in allowed_fieldtypes
		):
			field["name"] = field.get("fieldname")
			res.append(field)

	return res

def get_fields_meta(DocField, doctype, allowed_fieldtypes, restricted_fields):
	parent = "parent" if DocField._table_name == "tabDocField" else "dt"
	return (
		frappe.qb.from_(DocField)
		.select(
			DocField.fieldname,
			DocField.fieldtype,
			DocField.label,
			DocField.name,
			DocField.options,
		)
		.where(DocField[parent] == doctype)
		.where(DocField.hidden == False)
		.where(Criterion.any([DocField.fieldtype == i for i in allowed_fieldtypes]))
		.where(Criterion.all([DocField.fieldname != i for i in restricted_fields]))
		.run(as_dict=True)
	)

@frappe.whitelist()
def get_list_data(
	doctype: str,
	filters: dict,
	order_by: str,
	page_length=20,
	page_length_count=20,
	columns=None,
	rows=None,
	custom_view_name=None,
	default_filters=None,
):
	custom_view = False
	filters = frappe._dict(filters)

	for key in filters:
		value = filters[key]
		if isinstance(value, list):
			if "@me" in value:
				value[value.index("@me")] = frappe.session.user
			elif "%@me%" in value:
				index = [i for i, v in enumerate(value) if v == "%@me%"]
				for i in index:
					value[i] = "%" + frappe.session.user + "%"
		elif value == "@me":
			filters[key] = frappe.session.user

	if default_filters:
		default_filters = frappe.parse_json(default_filters)
		filters.update(default_filters)

	is_default = True
	if columns or rows:
		custom_view = True
		is_default = False
		columns = frappe.parse_json(columns)
		rows = frappe.parse_json(rows)

	if not columns:
		columns = [
			{"label": "Name", "type": "Data", "key": "name", "width": "16rem"},
			{"label": "Last Modified", "type": "Datetime", "key": "modified", "width": "8rem"},
		]

	if not rows:
		rows = ["name"]

	if not custom_view and frappe.db.exists("CRM View Settings", doctype):
		list_view_settings = frappe.get_doc("CRM View Settings", doctype)
		columns = frappe.parse_json(list_view_settings.columns)
		rows = frappe.parse_json(list_view_settings.rows)
		is_default = False
	elif not custom_view or is_default:
		_list = get_controller(doctype)

		if hasattr(_list, "default_list_data"):
			columns = _list.default_list_data().get("columns")
			rows = _list.default_list_data().get("rows")

	# check if rows has all keys from columns if not add them
	for column in columns:
		if column.get("key") not in rows:
			rows.append(column.get("key"))

	data = frappe.get_all(
		doctype,
		fields=rows,
		filters=filters,
		order_by=order_by,
		page_length=page_length,
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
		{"label": "Assigned To", "type": "Text", "value": "_assign"},
		{"label": "Owner", "type": "Link", "value": "owner", "options": "User"},
	]

	for field in std_fields:
		if field.get('value') not in rows:
			rows.append(field.get('value'))
		if field not in fields:
			fields.append(field)

	if not is_default and custom_view_name:
		is_default = frappe.db.get_value("CRM View Settings", custom_view_name, "load_default_columns")

	return {
		"data": data,
		"columns": columns,
		"rows": rows,
		"fields": fields,
		"page_length": page_length,
		"page_length_count": page_length_count,
		"is_default": is_default,
		"views": get_views(doctype, is_view=True),
		"total_count": frappe.client.get_count(doctype, filters=filters),
		"row_count": len(data),
	}


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
				"name": field.fieldname,
				"opened": True,
				"fields": [],
			}
		else:
			section_fields.append(get_field_obj(field))

	section_fields = []
	for section in sections:
		section_fields.append(sections[section])

	fields = [field for field in fields if field.fieldtype not in "Tab Break"]
	fields_meta = {}
	for field in fields:
		fields_meta[field.fieldname] = field

	return section_fields, fields_meta


def get_field_obj(field):
	obj = {
		"label": field.label,
		"type": get_type(field),
		"name": field.fieldname,
		"hidden": field.hidden,
		"reqd": field.reqd,
		"read_only": field.read_only,
	}

	obj["placeholder"] = "Add " + field.label + "..."

	if field.fieldtype == "Link":
		obj["placeholder"] = "Select " + field.label + "..."
		obj["doctype"] = field.options
	elif field.fieldtype == "Select" and field.options:
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

def get_assigned_users(doctype, name):
	assigned_users = frappe.get_all(
		"ToDo",
		fields=["allocated_to"],
		filters={
			"reference_type": doctype,
			"reference_name": name,
			"status": ("!=", "Cancelled"),
		},
		pluck="allocated_to",
	)

	return list(set(assigned_users))
