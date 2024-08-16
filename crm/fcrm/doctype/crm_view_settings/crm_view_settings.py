# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import json
import frappe
from frappe.model.document import Document, get_controller
from frappe.utils import parse_json


class CRMViewSettings(Document):
	pass

@frappe.whitelist()
def create(view):
	view = frappe._dict(view)

	view.filters = parse_json(view.filters) or {}
	view.columns = parse_json(view.columns or '[]')
	view.rows = parse_json(view.rows or '[]')
	view.kanban_columns = parse_json(view.kanban_columns or '[]')
	view.kanban_fields = parse_json(view.kanban_fields or '[]')

	default_rows = sync_default_rows(view.doctype)
	view.rows = view.rows + default_rows if default_rows else view.rows
	view.rows = remove_duplicates(view.rows)

	if not view.kanban_columns and view.type == "kanban":
		view.kanban_columns = sync_default_columns(view)
	elif not view.columns:
		view.columns = sync_default_columns(view)

	doc = frappe.new_doc("CRM View Settings")
	doc.name = view.label
	doc.label = view.label
	doc.type = view.type or 'list'
	doc.icon = view.icon
	doc.dt = view.doctype
	doc.user = frappe.session.user
	doc.route_name = view.route_name or ""
	doc.load_default_columns = view.load_default_columns or False
	doc.filters = json.dumps(view.filters)
	doc.order_by = view.order_by
	doc.group_by_field = view.group_by_field
	doc.column_field = view.column_field
	doc.title_field = view.title_field
	doc.kanban_columns = json.dumps(view.kanban_columns)
	doc.kanban_fields = json.dumps(view.kanban_fields)
	doc.columns = json.dumps(view.columns)
	doc.rows = json.dumps(view.rows)
	doc.insert()
	return doc

@frappe.whitelist()
def update(view):
	view = frappe._dict(view)

	filters = parse_json(view.filters or {})
	columns = parse_json(view.columns or [])
	rows = parse_json(view.rows or [])
	kanban_columns = parse_json(view.kanban_columns or [])
	kanban_fields = parse_json(view.kanban_fields or [])

	default_rows = sync_default_rows(view.doctype)
	rows = rows + default_rows if default_rows else rows
	rows = remove_duplicates(rows)

	doc = frappe.get_doc("CRM View Settings", view.name)
	doc.label = view.label
	doc.type = view.type or 'list'
	doc.icon = view.icon
	doc.route_name = view.route_name or ""
	doc.load_default_columns = view.load_default_columns or False
	doc.filters = json.dumps(filters)
	doc.order_by = view.order_by
	doc.group_by_field = view.group_by_field
	doc.column_field = view.column_field
	doc.title_field = view.title_field
	doc.kanban_columns = json.dumps(kanban_columns)
	doc.kanban_fields = json.dumps(kanban_fields)
	doc.columns = json.dumps(columns)
	doc.rows = json.dumps(rows)
	doc.save()
	return doc

@frappe.whitelist()
def delete(name):
	if frappe.db.exists("CRM View Settings", name):
		frappe.delete_doc("CRM View Settings", name)

@frappe.whitelist()
def public(name, value):
	if frappe.session.user != "Administrator" and "Sales Manager" not in frappe.get_roles():
		frappe.throw("Not permitted", frappe.PermissionError)

	doc = frappe.get_doc("CRM View Settings", name)
	if doc.pinned:
		doc.pinned = False
	doc.public = value
	doc.user = "" if value else frappe.session.user
	doc.save()

@frappe.whitelist()
def pin(name, value):
	doc = frappe.get_doc("CRM View Settings", name)
	doc.pinned = value
	doc.save()

def remove_duplicates(l):
	return list(dict.fromkeys(l))

def sync_default_rows(doctype, type="list"):
	list = get_controller(doctype)
	rows = []

	if hasattr(list, "default_list_data"):
		rows = list.default_list_data().get("rows")

	return rows

def sync_default_columns(view):
	list = get_controller(view.doctype)
	columns = []

	if view.type == "kanban" and view.column_field:
		field_meta = frappe.get_meta(view.doctype).get_field(view.column_field)
		if field_meta.fieldtype == "Link":
			columns = frappe.get_all(
				field_meta.options,
				fields=["name"],
				order_by="modified asc",
			)
		elif field_meta.fieldtype == "Select":
			columns = [{"name": option} for option in field_meta.options.split("\n")]
	elif hasattr(list, "default_list_data"):
		columns = list.default_list_data().get("columns")

	return columns


@frappe.whitelist()
def create_or_update_default_view(view):
	view = frappe._dict(view)

	filters = parse_json(view.filters) or {}
	columns = parse_json(view.columns or '[]')
	rows = parse_json(view.rows or '[]')
	kanban_columns = parse_json(view.kanban_columns or '[]')
	kanban_fields = parse_json(view.kanban_fields or '[]')

	default_rows = sync_default_rows(view.doctype, view.type)
	rows = rows + default_rows if default_rows else rows
	rows = remove_duplicates(rows)

	if not kanban_columns and view.type == "kanban":
		kanban_columns = sync_default_columns(view)
	elif not columns:
		columns = sync_default_columns(view)

	doc = frappe.db.exists(
		"CRM View Settings",
		{
			"dt": view.doctype,
			"type": view.type or 'list',
			"is_default": True,
			"user": frappe.session.user
		},
	)
	if doc:
		doc = frappe.get_doc("CRM View Settings", doc)
		doc.label = view.label
		doc.type = view.type or 'list'
		doc.route_name = view.route_name or ""
		doc.load_default_columns = view.load_default_columns or False
		doc.filters = json.dumps(filters)
		doc.order_by = view.order_by
		doc.group_by_field = view.group_by_field
		doc.column_field = view.column_field
		doc.title_field = view.title_field
		doc.kanban_columns = json.dumps(kanban_columns)
		doc.kanban_fields = json.dumps(kanban_fields)
		doc.columns = json.dumps(columns)
		doc.rows = json.dumps(rows)
		doc.save()
	else:
		doc = frappe.new_doc("CRM View Settings")
		label = 'Group By View' if view.type == 'group_by' else 'List View'
		doc.name = view.label or label
		doc.label = view.label or label
		doc.type = view.type or 'list'
		doc.dt = view.doctype
		doc.user = frappe.session.user
		doc.route_name = view.route_name or ""
		doc.load_default_columns = view.load_default_columns or False
		doc.filters = json.dumps(filters)
		doc.order_by = view.order_by
		doc.group_by_field = view.group_by_field
		doc.column_field = view.column_field
		doc.title_field = view.title_field
		doc.kanban_columns = json.dumps(kanban_columns)
		doc.kanban_fields = json.dumps(kanban_fields)
		doc.columns = json.dumps(columns)
		doc.rows = json.dumps(rows)
		doc.is_default = True
		doc.insert()