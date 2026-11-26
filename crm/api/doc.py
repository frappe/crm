import frappe

from crm.api import list_view
from crm.api import record as record_api
from crm.api.list_query import KanbanQuery, ListQuery, get_count, prepare_filters
from crm.api.views import get_views


def replaced_by(path):
	"""Mark a whitelisted method as kept for old callers, naming the method that replaces it."""

	def decorate(fn):
		fn.replaced_by = path
		return fn

	return decorate


@replaced_by("crm.api.list_view.get_list_view")
@frappe.whitelist()
def get_data(
	doctype: str,
	filters: dict,
	order_by: str,
	page_length: int = 20,
	page_length_count: int = 20,
	column_field: str | None = None,
	title_field: str | None = None,
	columns: str | list | None = None,
	rows: str | list | None = None,
	kanban_columns: str | list | None = None,
	kanban_fields: str | list | None = None,
	view: str | dict | None = None,
	default_filters: dict | None = None,
):
	"""Deprecated: use crm.api.list_view.get_list_view."""
	view = frappe.parse_json(view) or {}
	view_type = view.get("view_type")
	group_by_field = view.get("group_by_field")
	filters = prepare_filters(doctype, filters, default_filters)
	columns = frappe.parse_json(columns or "[]")
	rows = frappe.parse_json(rows or "[]")
	kanban_columns = frappe.parse_json(kanban_columns or "[]")
	kanban_fields = frappe.parse_json(kanban_fields or "[]")
	is_default = True

	if view_type == "kanban":
		query = KanbanQuery(doctype, filters, order_by, column_field)
		query.run(kanban_columns, title_field, kanban_fields, rows)
		data, rows = query.columns, query.rows
		kanban_columns, title_field, kanban_fields = (
			query.kanban_columns,
			query.title_field,
			query.kanban_fields,
		)
	else:
		query = ListQuery(doctype, filters, order_by, page_length, view_type, group_by_field)
		query.run(columns, rows)
		data, columns, rows, is_default = query.records, query.columns, query.rows, query.is_default

	fields = list_view.get_column_fields(doctype)
	for field in list_view.STANDARD_COLUMN_FIELDS:
		if field["fieldname"] not in rows:
			rows.append(field["fieldname"])

	if not is_default and view.get("custom_view_name"):
		is_default = frappe.db.get_value(
			"CRM View Settings", view["custom_view_name"], "load_default_columns"
		)

	if group_by_field and view_type == "group_by":
		group_by_field = get_group_by_field(fields, group_by_field, data, order_by)

	scripts = list_view.get_list_scripts(doctype)
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
		"total_count": get_count(doctype, filters),
		"row_count": len(data),
		"form_script": scripts["form_script"],
		"list_script": scripts["list_script"],
		"view_type": view_type,
	}


def get_group_by_field(fields, fieldname, data, order_by):
	"""The group by field with its group values, as get_data returns it."""
	field = next((f for f in fields if f.get("fieldname") == fieldname), None)
	if not field:
		return fieldname

	if field.get("fieldtype") == "Select":
		options = field.get("options").split("\n")
	else:
		options = get_group_values(data, fieldname, order_by)

	return {
		"label": field.get("label"),
		"fieldname": fieldname,
		"fieldtype": field.get("fieldtype"),
		"options": options,
	}


def get_group_values(data, fieldname, order_by):
	values = [value for value in {d.get(fieldname) for d in data} if value]
	if any(not d.get(fieldname) for d in data):
		values.append("")
	if not (order_by and fieldname in order_by):
		return sorted(values)

	order_by_fields = [(part.split(" ")[0], part.split(" ")[1]) for part in order_by.split(",")]
	if (fieldname, "asc") in order_by_fields:
		return sorted(values)
	if (fieldname, "desc") in order_by_fields:
		return sorted(values, reverse=True)
	return values


@replaced_by("crm.api.list_view.get_sort_fields")
@frappe.whitelist()
def sort_options(doctype: str):
	"""Deprecated: use crm.api.list_view.get_sort_fields."""
	return list_view.get_sort_fields(doctype)


@replaced_by("crm.api.list_view.get_filter_fields")
@frappe.whitelist()
def get_filterable_fields(doctype: str):
	"""Deprecated: use crm.api.list_view.get_filter_fields."""
	return list_view.get_filter_fields(doctype)


@replaced_by("crm.api.list_view.get_group_by_fields")
@frappe.whitelist()
def get_group_by_fields(doctype: str):
	"""Deprecated: use crm.api.list_view.get_group_by_fields."""
	return list_view.get_group_by_fields(doctype)


@replaced_by("crm.api.list_view.get_quick_filters")
@frappe.whitelist()
def get_quick_filters(doctype: str, cached: bool = True):
	"""Deprecated: use crm.api.list_view.get_quick_filters."""
	return list_view.get_quick_filters(doctype, cached)


@replaced_by("crm.api.list_view.set_quick_filters")
@frappe.whitelist(methods=["POST"])
def update_quick_filters(quick_filters: str | list, old_filters: str | list, doctype: str):
	"""Deprecated: use crm.api.list_view.set_quick_filters."""
	list_view.set_quick_filters(doctype, frappe.parse_json(quick_filters) or [])


@frappe.whitelist()
def get_fields(doctype: str, allow_all_fieldtypes: bool = False):
	not_allowed_fieldtypes = [*list(frappe.model.no_value_fields), "Read Only"]
	if allow_all_fieldtypes:
		not_allowed_fieldtypes = []
	fields = frappe.get_meta(doctype).fields

	_fields = []

	for field in fields:
		if field.fieldtype not in not_allowed_fieldtypes and field.fieldname:
			_fields.append(field)

	return _fields


@replaced_by("crm.api.record.get_assignees")
@frappe.whitelist()
def get_assigned_users(doctype: str, name: str | int, default_assigned_to: str | None = None):
	"""Deprecated: use crm.api.record.get_assignees."""
	return record_api.get_assignees(doctype, name) or ([default_assigned_to] if default_assigned_to else [])


@replaced_by("crm.api.record.remove_assignees")
@frappe.whitelist()
def remove_assignments(doctype: str, name: str, assignees: str | list):
	"""Deprecated: use crm.api.record.remove_assignees."""
	record_api.remove_assignees(doctype, name, frappe.parse_json(assignees) or [])


@replaced_by("crm.api.record.mark_as_seen")
@frappe.whitelist()
def add_seen(doctype: str, name: str):
	"""Deprecated: use crm.api.record.mark_as_seen."""
	record_api.mark_as_seen(doctype, name)


@replaced_by("crm.api.record.get_linked_records")
@frappe.whitelist()
def get_linked_docs_of_document(doctype: str, docname: str):
	"""Deprecated: use crm.api.record.get_linked_records."""
	return record_api.get_linked_records(doctype, docname)


@replaced_by("crm.api.record.unlink_records")
@frappe.whitelist()
def remove_linked_doc_reference(items: str | list, remove_contact: bool = False, delete: bool = False):
	"""Deprecated: use crm.api.record.unlink_records."""
	record_api.unlink_records(frappe.parse_json(items), remove_contact, delete)
	return "success"


@replaced_by("crm.api.record.delete_records")
@frappe.whitelist()
def delete_bulk_docs(doctype: str, items: str | list, delete_linked: bool = False):
	"""Deprecated: use crm.api.record.delete_records."""
	record_api.delete_records(doctype, frappe.parse_json(items) or [], delete_linked)
	return "success"
