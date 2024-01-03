# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import json
import frappe
from frappe.model.document import Document, get_controller


class CRMViewSettings(Document):
	pass

@frappe.whitelist()
def create(view, duplicate=False):
	view = frappe._dict(view)

	if duplicate:
		view.filters = json.loads(view.filters)
		view.columns = json.loads(view.columns)
		view.rows = json.loads(view.rows)

	doc = frappe.new_doc("CRM View Settings")
	doc.name = view.label
	doc.label = view.label
	doc.dt = view.doctype
	doc.user = frappe.session.user
	doc.filters = json.dumps(view.filters)
	doc.order_by = view.order_by
	doc.route_name = view.route_name or ""
	doc.load_default_columns = view.load_default_columns or False

	if not view.columns:
		view.columns = []
	if not view.rows:
		view.rows = []

	default_rows = sync_default_list_rows(view.doctype)

	if default_rows:
		view.rows = view.rows + default_rows

	view.rows = remove_duplicates(view.rows)

	doc.columns = json.dumps(view.columns)
	doc.rows = json.dumps(view.rows)
	doc.insert()
	return doc

@frappe.whitelist()
def update(view):
	view = frappe._dict(view)
	default_rows = sync_default_list_rows(view.doctype)
	columns = view.columns or []
	filters = view.filters
	rows = view.rows or []
	default_columns = view.default_columns or False

	if default_rows:
		rows = rows + default_rows

	rows = remove_duplicates(rows)

	doc = frappe.get_doc("CRM View Settings", view.name)
	doc.label = view.label
	doc.route_name = view.route_name or ""
	doc.load_default_columns = view.load_default_columns or False
	doc.filters = json.dumps(filters)
	doc.order_by = view.order_by
	doc.columns = json.dumps(columns)
	doc.rows = json.dumps(rows)
	doc.save()
	return doc

@frappe.whitelist()
def delete(name):
	if frappe.db.exists("CRM View Settings", name):
		frappe.delete_doc("CRM View Settings", name)

@frappe.whitelist()
def pin(name, value):
	doc = frappe.get_doc("CRM View Settings", name)
	doc.pinned = value
	doc.save()

def remove_duplicates(l):
	return list(dict.fromkeys(l))

def sync_default_list_rows(doctype):
	list = get_controller(doctype)
	rows = []

	if hasattr(list, "default_list_data"):
		rows = list.default_list_data().get("rows")

	return rows
