import frappe
import json
from frappe import _
from frappe.model.document import get_controller
from frappe.model import no_value_fields
from pypika import Criterion
from frappe.utils import make_filter_tuple

from crm.api.views import get_views
from crm.fcrm.doctype.crm_form_script.crm_form_script import get_form_script


@frappe.whitelist()
def sort_options(doctype: str):
	fields = frappe.get_meta(doctype).fields
	fields = [field for field in fields if field.fieldtype not in no_value_fields]
	fields = [
		{
			"label": _(field.label),
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
		field["label"] = _(field["label"])
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
		"Dynamic Link",
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
	doc_fields = get_doctype_fields_meta(DocField, doctype, allowed_fieldtypes, restricted_fields)
	res.extend(doc_fields)

	# append Custom Fields
	CustomField = frappe.qb.DocType("Custom Field")
	custom_fields = get_doctype_fields_meta(CustomField, doctype, allowed_fieldtypes, restricted_fields)
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
		{"fieldname": "_liked_by", "fieldtype": "Data", "label": "Like"},
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

	for field in res:
		field["label"] = _(field.get("label"))

	return res


@frappe.whitelist()
def get_group_by_fields(doctype: str):
	allowed_fieldtypes = [
		"Check",
		"Data",
		"Float",
		"Int",
		"Currency",
		"Dynamic Link",
		"Link",
		"Select",
		"Duration",
		"Date",
		"Datetime",
	]

	fields = frappe.get_meta(doctype).fields
	fields = [field for field in fields if field.fieldtype not in no_value_fields and field.fieldtype in allowed_fieldtypes]
	fields = [
		{
			"label": _(field.label),
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
		{"label": "Liked By", "value": "_liked_by"},
		{"label": "Assigned To", "value": "_assign"},
		{"label": "Comments", "value": "_comments"},
		{"label": "Created On", "value": "creation"},
		{"label": "Modified On", "value": "modified"},
	]

	for field in standard_fields:
		field["label"] = _(field["label"])
		fields.append(field)

	return fields


def get_doctype_fields_meta(DocField, doctype, allowed_fieldtypes, restricted_fields):
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
def get_quick_filters(doctype: str):
	meta = frappe.get_meta(doctype)
	fields = [field for field in meta.fields if field.in_standard_filter]
	quick_filters = []

	for field in fields:

		if field.fieldtype == "Select":
			field.options = field.options.split("\n")
			field.options = [{"label": option, "value": option} for option in field.options]
			field.options.insert(0, {"label": "", "value": ""})
		quick_filters.append({
			"label": _(field.label),
			"name": field.fieldname,
			"type": field.fieldtype,
			"options": field.options,
		})

	if doctype == "CRM Lead":
		quick_filters = [filter for filter in quick_filters if filter.get("name") != "converted"]

	return quick_filters

@frappe.whitelist()
def get_data(
	doctype: str,
	filters: dict,
	order_by: str,
	page_length=20,
	page_length_count=20,
	column_field=None,
	title_field=None,
	columns=[],
	rows=[],
	kanban_columns=[],
	kanban_fields=[],
	view=None,
	default_filters=None,
):
	custom_view = False
	filters = frappe._dict(filters)
	rows = frappe.parse_json(rows or "[]")
	columns = frappe.parse_json(columns or "[]")
	kanban_fields = frappe.parse_json(kanban_fields or "[]")
	kanban_columns = frappe.parse_json(kanban_columns or "[]")

	custom_view_name = view.get('custom_view_name') if view else None
	view_type = view.get('view_type') if view else None
	group_by_field = view.get('group_by_field') if view else None

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
	data = []
	_list = get_controller(doctype)
	default_rows = []
	if hasattr(_list, "default_list_data"):
		default_rows = _list.default_list_data().get("rows")

	if view_type != "kanban":
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

		default_view_filters = {
			"dt": doctype,
			"type": view_type or 'list',
			"is_default": 1,
			"user": frappe.session.user,
		}

		if not custom_view and frappe.db.exists("CRM View Settings", default_view_filters):
			list_view_settings = frappe.get_doc("CRM View Settings", default_view_filters)
			columns = frappe.parse_json(list_view_settings.columns)
			rows = frappe.parse_json(list_view_settings.rows)
			is_default = False
		elif not custom_view or is_default and hasattr(_list, "default_list_data"):
			rows = default_rows
			columns = _list.default_list_data().get("columns")

		# check if rows has all keys from columns if not add them
		for column in columns:
			if column.get("key") not in rows:
				rows.append(column.get("key"))
			column["label"] = _(column.get("label"))

			if column.get("key") == "_liked_by" and column.get("width") == "10rem":
				column["width"] = "50px"

		# check if rows has group_by_field if not add it
		if group_by_field and group_by_field not in rows:
			rows.append(group_by_field)

		data = frappe.get_list(
			doctype,
			fields=rows,
			filters=filters,
			order_by=order_by,
			page_length=page_length,
		) or []

	if view_type == "kanban":
		if not rows:
			rows = default_rows

		if not kanban_columns and column_field:
			field_meta = frappe.get_meta(doctype).get_field(column_field)
			if field_meta.fieldtype == "Link":
				kanban_columns = frappe.get_all(
					field_meta.options,
					fields=["name"],
					order_by="modified asc",
				)
			elif field_meta.fieldtype == "Select":
				kanban_columns = [{"name": option} for option in field_meta.options.split("\n")]

		if not title_field:
			title_field = "name"
			if hasattr(_list, "default_kanban_settings"):
				title_field = _list.default_kanban_settings().get("title_field")

		if title_field not in rows:
			rows.append(title_field)

		if not kanban_fields:
			kanban_fields = ["name"]
			if hasattr(_list, "default_kanban_settings"):
				kanban_fields = json.loads(_list.default_kanban_settings().get("kanban_fields"))

		for field in kanban_fields:
			if field not in rows:
				rows.append(field)

		for kc in kanban_columns:
			column_filters = { column_field: kc.get('name') }
			order = kc.get("order")
			if column_field in filters and filters.get(column_field) != kc.name or kc.get('delete'):
				column_data = []
			else:
				column_filters.update(filters.copy())
				page_length = 20

				if kc.get("page_length"):
					page_length = kc.get("page_length")

				if order:
					column_data = get_records_based_on_order(doctype, rows, column_filters, page_length, order)
				else:
					column_data = frappe.get_list(
						doctype,
						fields=rows,
						filters=convert_filter_to_tuple(doctype, column_filters),
						order_by=order_by,
						page_length=page_length,
					)

				new_filters = filters.copy()
				new_filters.update({ column_field: kc.get('name') })

				all_count = len(frappe.get_list(doctype, filters=convert_filter_to_tuple(doctype, new_filters)))

				kc["all_count"] = all_count
				kc["count"] = len(column_data)

				for d in column_data:
					getCounts(d, doctype)

			if order:
				column_data = sorted(
					column_data, key=lambda x: order.index(x.get("name"))
					if x.get("name") in order else len(order)
				)

			data.append({"column": kc, "fields": kanban_fields, "data": column_data})

	fields = frappe.get_meta(doctype).fields
	fields = [field for field in fields if field.fieldtype not in no_value_fields]
	fields = [
		{
			"label": _(field.label),
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
		{"label": "Like", "type": "Data", "value": "_liked_by"},
	]

	for field in std_fields:
		if field.get('value') not in rows:
			rows.append(field.get('value'))
		if field not in fields:
			field["label"] = _(field["label"])
			fields.append(field)

	if not is_default and custom_view_name:
		is_default = frappe.db.get_value("CRM View Settings", custom_view_name, "load_default_columns")

	if group_by_field and view_type == "group_by":
		def get_options(type, options):
			if type == "Select":
				return [option for option in options.split("\n")]
			else:
				has_empty_values = any([not d.get(group_by_field) for d in data])
				options = list(set([d.get(group_by_field) for d in data]))
				options = [u for u in options if u]
				if has_empty_values:
					options.append("")

				if order_by and group_by_field in order_by:
					order_by_fields = order_by.split(",")
					order_by_fields = [(field.split(" ")[0], field.split(" ")[1]) for field in order_by_fields]
					if (group_by_field, "asc") in order_by_fields:
						options.sort()
					elif (group_by_field, "desc") in order_by_fields:
						options.sort(reverse=True)
				else:
					options.sort()
				return options

		for field in fields:
			if field.get("value") == group_by_field:
				group_by_field = {
					"label": field.get("label"),
					"name": field.get("value"),
					"type": field.get("type"),
					"options": get_options(field.get("type"), field.get("options")),
				}

	return {
		"data": data,
		"columns": columns,
		"rows": rows,
		"fields": fields,
		"column_field": column_field,
		"title_field": title_field,
		"kanban_columns": kanban_columns,
		"kanban_fields": kanban_fields,
		"group_by_field": group_by_field,
		"page_length": page_length,
		"page_length_count": page_length_count,
		"is_default": is_default,
		"views": get_views(doctype),
		"total_count": len(frappe.get_list(doctype, filters=filters)),
		"row_count": len(data),
		"form_script": get_form_script(doctype),
		"list_script": get_form_script(doctype, "List"),
		"view_type": view_type,
	}

def convert_filter_to_tuple(doctype, filters):
	if isinstance(filters, dict):
		filters_items = filters.items()
		filters = []
		for key, value in filters_items:
			filters.append(make_filter_tuple(doctype, key, value))
	return filters


def get_records_based_on_order(doctype, rows, filters, page_length, order):
	records = []
	filters = convert_filter_to_tuple(doctype, filters)
	in_filters = filters.copy()
	in_filters.append([doctype, "name", "in", order[:page_length]])
	records = frappe.get_list(
		doctype,
		fields=rows,
		filters=in_filters,
		order_by="creation desc",
		page_length=page_length,
	)

	if len(records) < page_length:
		not_in_filters = filters.copy()
		not_in_filters.append([doctype, "name", "not in", order])
		remaining_records = frappe.get_list(
			doctype,
			fields=rows,
			filters=not_in_filters,
			order_by="creation desc",
			page_length=page_length - len(records),
		)
		for record in remaining_records:
			records.append(record)

	return records

@frappe.whitelist()
def get_fields_meta(doctype, restricted_fieldtypes=None, as_array=False):
	not_allowed_fieldtypes = [
		"Tab Break",
		"Section Break",
		"Column Break",
	]

	if restricted_fieldtypes:
		restricted_fieldtypes = frappe.parse_json(restricted_fieldtypes)
		not_allowed_fieldtypes += restricted_fieldtypes

	fields = frappe.get_meta(doctype).fields
	fields = [field for field in fields if field.fieldtype not in not_allowed_fieldtypes]

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
		{"fieldname": "_liked_by", "fieldtype": "Data", "label": "Like"},
		{"fieldname": "_comments", "fieldtype": "Text", "label": "Comments"},
		{"fieldname": "_assign", "fieldtype": "Text", "label": "Assigned To"},
		{"fieldname": "creation", "fieldtype": "Datetime", "label": "Created On"},
		{"fieldname": "modified", "fieldtype": "Datetime", "label": "Last Updated On"},
	]

	for field in standard_fields:
		if not restricted_fieldtypes or field.get('fieldtype') not in restricted_fieldtypes:
			fields.append(field)

	if as_array:
		return fields

	fields_meta = {}
	for field in fields:
		fields_meta[field.get('fieldname')] = field

	return fields_meta

@frappe.whitelist()
def get_sidebar_fields(doctype, name):
	if not frappe.db.exists("CRM Fields Layout", {"dt": doctype, "type": "Side Panel"}):
		return []
	layout = frappe.get_doc("CRM Fields Layout", {"dt": doctype, "type": "Side Panel"}).layout

	if not layout:
		return []
	
	layout = json.loads(layout)

	not_allowed_fieldtypes = [
		"Tab Break",
		"Section Break",
		"Column Break",
	]

	fields = frappe.get_meta(doctype).fields
	fields = [field for field in fields if field.fieldtype not in not_allowed_fieldtypes]

	doc = frappe.get_cached_doc(doctype, name)
	has_high_permlevel_fields = any(df.permlevel > 0 for df in fields)
	if has_high_permlevel_fields:
		has_read_access_to_permlevels = doc.get_permlevel_access("read")
		has_write_access_to_permlevels = doc.get_permlevel_access("write")

	for section in layout:
		section["name"] = section.get("name") or section.get("label")
		for field in section.get("fields") if section.get("fields") else []:
			field_obj = next((f for f in fields if f.fieldname == field), None)
			if field_obj:
				if field_obj.permlevel > 0:
					field_has_write_access = field_obj.permlevel in has_write_access_to_permlevels
					field_has_read_access = field_obj.permlevel in has_read_access_to_permlevels
					if not field_has_write_access and field_has_read_access:
						field_obj.read_only = 1
					if not field_has_read_access and not field_has_write_access:
						field_obj.hidden = 1
				section["fields"][section.get("fields").index(field)] = get_field_obj(field_obj)

	fields_meta = {}
	for field in fields:
		fields_meta[field.fieldname] = field

	return layout

def get_field_obj(field):
	obj = {
		"label": field.label,
		"type": get_type(field),
		"name": field.fieldname,
		"hidden": field.hidden,
		"reqd": field.reqd,
		"read_only": field.read_only,
		"all_properties": field,
	}

	obj["placeholder"] = field.get("placeholder") or "Add " + field.label + "..."

	if field.fieldtype == "Link":
		obj["placeholder"] = field.get("placeholder") or "Select " + field.label + "..."
		obj["doctype"] = field.options
	elif field.fieldtype == "Select" and field.options:
		obj["placeholder"] = field.get("placeholder") or "Select " + field.label + "..."
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

def get_assigned_users(doctype, name, default_assigned_to=None):
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

	users = list(set(assigned_users))

	# if users is empty, add default_assigned_to
	if not users and default_assigned_to:
		users = [default_assigned_to]
	return users


@frappe.whitelist()
def get_fields(doctype: str, allow_all_fieldtypes: bool = False):
	not_allowed_fieldtypes = list(frappe.model.no_value_fields) + ["Read Only"]
	if allow_all_fieldtypes:
		not_allowed_fieldtypes = []
	fields = frappe.get_meta(doctype).fields

	_fields = []

	for field in fields:
		if (
			field.fieldtype not in not_allowed_fieldtypes
			and field.fieldname
		):
			_fields.append({
				"label": field.label,
				"type": field.fieldtype,
				"value": field.fieldname,
				"options": field.options,
				"mandatory": field.reqd,
				"read_only": field.read_only,
				"hidden": field.hidden,
				"depends_on": field.depends_on,
				"mandatory_depends_on": field.mandatory_depends_on,
				"read_only_depends_on": field.read_only_depends_on,
				"link_filters": field.get("link_filters"),
				"placeholder": field.get("placeholder"),
			})

	return _fields


def getCounts(d, doctype):
	d["_email_count"] = frappe.db.count("Communication", filters={"reference_doctype": doctype, "reference_name": d.get("name"), "communication_type": "Communication"}) or 0
	d["_email_count"] = d["_email_count"] + frappe.db.count("Communication", filters={"reference_doctype": doctype, "reference_name": d.get("name"), "communication_type": "Automated Message"})
	d["_comment_count"] = frappe.db.count("Comment", filters={"reference_doctype": doctype, "reference_name": d.get("name"), "comment_type": "Comment"})
	d["_task_count"] = frappe.db.count("CRM Task", filters={"reference_doctype": doctype, "reference_docname": d.get("name")})
	d["_note_count"] = frappe.db.count("FCRM Note", filters={"reference_doctype": doctype, "reference_docname": d.get("name")})
	return d