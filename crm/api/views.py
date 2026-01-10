import json

import frappe
from frappe.query_builder import Order
from pypika import Criterion


@frappe.whitelist()
def get_views(doctype=None):
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
def get_current_view(doctype=None, view_name=None):
	View = frappe.qb.DocType("CRM View Settings")
	query = frappe.qb.from_(View).select("*")

	if view_name:
		query = query.where(View.name == view_name)
	else:
		query = (
			query.where(View.is_standard == 1)
			.where(Criterion.any([View.user == "", View.user == frappe.session.user]))
			.where(View.dt == doctype)
			.orderby("modified", order=Order.desc)
			.limit(1)
		)

	view = query.run(as_dict=True) or None

	if not view:
		return add_default_view(doctype)

	return view[0]


def add_default_view(doctype):
	columns = [
		{"label": "Like", "type": "Data", "key": "_liked_by", "width": "50px"},
		{"label": "Name", "type": "Data", "key": "name", "width": "16rem"},
		{"label": "Last Updated On", "type": "Datetime", "key": "modified", "width": "8rem"},
	]

	rows = ["name"]

	default_view = {
		"name": "Default View (" + doctype + ")",
		"label": "Default View",
		"type": "list",
		"dt": doctype,
		"columns": json.dumps(columns),
		"rows": json.dumps(rows),
		"filters": json.dumps({}),
		"order_by": "modified desc",
		"is_standard": 1,
	}

	return default_view
