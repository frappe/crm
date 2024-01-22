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

	default_rows = sync_default_list_rows(view.doctype)
	view.rows = view.rows + default_rows if default_rows else view.rows
	view.rows = remove_duplicates(view.rows)

	doc = frappe.new_doc("CRM View Settings")
	doc.name = view.label
	doc.label = view.label
	doc.is_view = True
	doc.dt = view.doctype
	doc.user = frappe.session.user
	doc.route_name = view.route_name or ""
	doc.load_default_columns = view.load_default_columns or False
	doc.filters = json.dumps(view.filters)
	doc.order_by = view.order_by
	doc.columns = json.dumps(view.columns)
	doc.rows = json.dumps(view.rows)
	doc.insert()
	return doc

@frappe.whitelist()
def update(view):
	view = frappe._dict(view)

	filters = parse_json(view.filters) or {}
	columns = parse_json(view.columns) or []
	rows = parse_json(view.rows) or []

	default_rows = sync_default_list_rows(view.doctype)
	rows = rows + default_rows if default_rows else rows
	rows = remove_duplicates(rows)

	doc = frappe.get_doc("CRM View Settings", view.name)
	doc.label = view.label
	doc.is_view = True
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
def public(name, value):
	if frappe.session.user != "Administrator" and "Sales Manager" not in frappe.get_roles():
		frappe.throw("Not permitted", frappe.PermissionError)

	doc = frappe.get_doc("CRM View Settings", name)
	doc.public = value
	doc.user = "" if value else frappe.session.user
	doc.save()

@frappe.whitelist()
def pin(name, value):
	doc = frappe.get_doc("CRM View Settings", name)
	doc.pinned = value
	doc.save()

@frappe.whitelist()
def make_default(name, doctype, route_name):
	existing_default_view = frappe.db.exists("CRM View Settings", {
		"default": True,
		"user": frappe.session.user
	})
	if existing_default_view:
		frappe.db.set_value("CRM View Settings", existing_default_view, "default", False)
	else:
		public_default = frappe.db.exists("CRM View Settings", {
			"default": True,
			"public": True
		})
		if public_default:
			public_default_view = frappe.get_doc("CRM View Settings", public_default)
			user_list = json.loads(public_default_view.user_list)
			if frappe.session.user in user_list:
				updated_user_list = [user for user in user_list if user != frappe.session.user]
				if not updated_user_list:
					public_default_view.default = False
					public_default_view.user_list = None
				else:
					public_default_view.user_list = json.dumps(updated_user_list)
				public_default_view.save()

	if not name and doctype:
		exists = frappe.db.exists("CRM View Settings", {
			"dt": doctype,
			"is_view": False,
			"user": frappe.session.user
		})
		if not exists:
			doc = frappe.new_doc("CRM View Settings")
			doc.label = "List View"
			doc.default = True
			doc.dt = doctype
			doc.route_name = route_name
			doc.user = frappe.session.user
			doc.is_view = False
			doc.insert()
		else:
			frappe.db.set_value("CRM View Settings", exists, "default", True)
	elif frappe.db.get_value("CRM View Settings", name, "public"):
		doc = frappe.get_doc("CRM View Settings", name)
		doc.default = True
		doc.user_list = (
			json.dumps([frappe.session.user])
			if not doc.user_list
			else json.dumps(json.loads(doc.user_list) + [frappe.session.user])
		)
		doc.save()
	else:
		frappe.db.set_value("CRM View Settings", name, "default", True)

def remove_duplicates(l):
	return list(dict.fromkeys(l))

def sync_default_list_rows(doctype):
	list = get_controller(doctype)
	rows = []

	if hasattr(list, "default_list_data"):
		rows = list.default_list_data().get("rows")

	return rows
