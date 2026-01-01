import json

import frappe
from pypika import Criterion


@frappe.whitelist()
def get_views(doctype):
	View = frappe.qb.DocType("CRM View Settings")
	query = (
		frappe.qb.from_(View)
		.select("*")
		.where(Criterion.any([View.user == "", View.user == frappe.session.user]))
	)
	if doctype:
		query = query.where(View.dt == doctype)
	views = query.run(as_dict=True)
	return views


@frappe.whitelist()
def get_doctype_views(doctype):
	View = frappe.qb.DocType("CRM View Settings")
	query = (
		frappe.qb.from_(View)
		.select("*")
		.where(Criterion.any([View.user == "", View.user == frappe.session.user]))
	)
	if doctype:
		query = query.where(View.dt == doctype)

	views = query.run(as_dict=True) or []

	if doctype:
		default_views = [view for view in views if view.get("is_default")]
		if not default_views:
			add_default_view(views, doctype)

	return views


def add_default_view(views, doctype):
	columns = [
		{"label": "Name", "type": "Data", "key": "name", "width": "16rem"},
		{"label": "Last Updated On", "type": "Datetime", "key": "modified", "width": "8rem"},
	]

	rows = ["name"]

	default_view = {
		"name": "Default View (" + doctype + ")",
		"label": "Default View",
		"is_default": 1,
		"type": "list",
		"dt": doctype,
		"columns": json.dumps(columns),
		"rows": json.dumps(rows),
		"filters": json.dumps({}),
		"order_by": "modified desc",
	}

	return views.append(default_view)
