import json

import frappe
from frappe.query_builder import Order
from pypika import Criterion


@frappe.whitelist()
def get_doctype_list():
	doctypes = (
		frappe.qb.from_("DocType")
		.select("name")
		.where(Criterion.all([frappe.qb.Field("issingle") == 0, frappe.qb.Field("istable") == 0]))
		.orderby("name")
		.run(as_dict=True)
	)
	return doctypes


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
		return add_standard_view(doctype)

	return view[0]


STANDARD_LIST_FIELDS = {
	"name": {"label": "Name", "fieldtype": "Data", "fieldname": "name", "width": "16rem"},
	"modified": {
		"label": "Last Updated On",
		"fieldtype": "Datetime",
		"fieldname": "modified",
		"width": "8rem",
	},
}


def ordered_fieldnames(title_field, fields):
	seen = set()
	ordered = []

	_fields = [f.get("fieldname") for f in fields if f.get("in_list_view")]

	def add_field(fieldname):
		if not fieldname or fieldname in seen:
			return
		seen.add(fieldname)
		ordered.append(fieldname)

	base_fields = [f for f in _fields if f not in {"name", "modified", title_field}]

	if title_field:
		add_field(title_field)
		for fieldname in base_fields:
			add_field(fieldname)
		add_field("name")
	else:
		add_field("name")
		for fieldname in base_fields:
			add_field(fieldname)

	add_field("modified")

	return ordered


def add_standard_view(doctype):
	columns = [{"label": "Like", "type": "Data", "key": "_liked_by", "width": "50px"}]
	rows = ["name"]

	meta = frappe.get_meta(doctype)
	fields = meta.get("fields") or []
	title_field = (meta.get("title_field") or "").strip() or None
	ordered_fields = ordered_fieldnames(title_field, fields)
	field_map = {f.get("fieldname"): f for f in fields if f.get("fieldname")}

	if title_field:
		STANDARD_LIST_FIELDS["name"]["width"] = "8rem"

	for fieldname in ordered_fields:
		field_def = STANDARD_LIST_FIELDS.get(fieldname) or field_map.get(fieldname)
		if not field_def:
			continue
		columns.append(
			{
				"label": field_def.get("label"),
				"type": field_def.get("fieldtype"),
				"key": field_def.get("fieldname"),
				"width": field_def.get("width") or "10rem",
			}
		)
		field_key = field_def.get("fieldname")
		if field_key and field_key not in rows:
			rows.append(field_key)

	standard_view = {
		"name": f"Standard view ({doctype})",
		"label": "List",
		"type": "list",
		"dt": doctype,
		"columns": json.dumps(columns),
		"rows": json.dumps(rows),
		"filters": json.dumps({}),
		"order_by": "modified desc",
		"is_standard": 1,
	}

	return standard_view
