import copy
import json
from typing import Literal

import frappe
from frappe import _
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.model import no_value_fields
from frappe.model.document import get_controller
from pypika import Criterion

from crm.api.list_defaults import MetaListDefaults
from crm.api.list_query import KanbanQuery, ListQuery, prepare_filters
from crm.fcrm.doctype.crm_form_script.crm_form_script import get_form_script

LEAN_COLUMN_KEYS = ("key", "label", "type", "width")


@frappe.whitelist(methods=["GET", "POST"])
def get_list_view(
	doctype: str,
	filters: dict | None = None,
	order_by: str | None = None,
	page_length: int = 20,
	view_name: str | int | None = None,
	view_type: Literal["list", "group_by"] | None = None,
	group_by_field: str | None = None,
	columns: list[dict] | None = None,
	fields: list[str] | None = None,
) -> dict:
	"""Return a page of records with their columns, total count and the view used.

	Arguments left out come from the saved view, then the user's standard view,
	then the doctype's defaults. Send filters, columns or fields with POST.
	doctype: the DocType to list.
	filters: field filters, such as {"status": "Open"}; "@me" is the current user.
	order_by: the sort, such as "modified desc".
	page_length: the number of records to return.
	view_name: a saved CRM View Settings to use.
	view_type: "list", or "group_by" to group the records by group_by_field.
	group_by_field: the field to group by; defaults to a Select field.
	columns: the columns to show, each a dict with key, label, type and width.
	fields: extra fields to fetch for each record.
	"""
	view = get_saved_view(doctype, view_name)
	view_type = view_type or view.type or "list"
	if view_type not in ("list", "group_by"):
		frappe.throw(_("Use get_kanban_view for a kanban view"))

	defaults = MetaListDefaults(frappe.get_meta(doctype))
	filters = filters if filters is not None else view.filters or {}
	order_by = order_by or view.order_by or defaults.order_by
	if view_type == "group_by":
		group_by_field = group_by_field or view.group_by_field or defaults.select_field

	query = ListQuery(
		doctype,
		prepare_filters(doctype, copy.deepcopy(filters)),
		order_by,
		page_length,
		view_type,
		group_by_field,
	).run(columns or view.columns, fields or view.rows)
	return {
		"records": query.records,
		"columns": [{key: column.get(key) for key in LEAN_COLUMN_KEYS} for column in query.columns],
		"total": query.total,
		"view": {
			"name": view_name,
			"type": view_type,
			"filters": filters,
			"order_by": order_by,
			"group_by_field": group_by_field,
		},
	}


@frappe.whitelist(methods=["GET", "POST"])
def get_kanban_view(
	doctype: str,
	filters: dict | None = None,
	order_by: str | None = None,
	view_name: str | int | None = None,
	column_field: str | None = None,
	title_field: str | None = None,
	card_fields: list[str] | None = None,
	kanban_columns: list[dict] | None = None,
) -> dict:
	"""Return the kanban columns of a doctype, each with a page of records.

	Arguments left out come from the saved view, then the doctype's defaults.
	With no Select field to use, columns is empty and column_field is None.
	Send filters, card_fields or kanban_columns with POST.
	doctype: the DocType to show.
	filters: field filters, such as {"status": "Open"}; "@me" is the current user.
	order_by: the sort within each column, such as "modified desc".
	view_name: a saved kanban CRM View Settings to use.
	column_field: the Select or Link field whose values are the columns.
	title_field: the field shown as each card's title.
	card_fields: the fields shown on each card.
	kanban_columns: the columns, each a dict with name and optional page_length.
	"""
	view = get_saved_view(doctype, view_name)
	defaults = MetaListDefaults(frappe.get_meta(doctype))
	filters = filters if filters is not None else view.filters or {}
	order_by = order_by or view.order_by or defaults.order_by
	query = KanbanQuery(doctype, prepare_filters(doctype, copy.deepcopy(filters)), order_by)
	query.column_field = column_field or view.column_field or query.default_column_field
	query.run(
		kanban_columns or view.kanban_columns,
		title_field or view.title_field,
		card_fields or view.kanban_fields,
	)
	return {
		"columns": [
			get_lean_kanban_column(column) for column in query.columns if not column["column"].get("delete")
		],
		"total": query.total,
		"view": {
			"name": view_name,
			"type": "kanban",
			"filters": filters,
			"order_by": order_by,
			"column_field": query.column_field,
			"title_field": query.title_field,
			"card_fields": query.kanban_fields,
		},
	}


@frappe.whitelist(methods=["GET"])
def get_sort_fields(doctype: str) -> list[dict]:
	"""Return the fields a doctype's list can be sorted by.

	doctype: the DocType.
	"""
	fields = [
		{"label": _(field.label), "value": field.fieldname, "fieldname": field.fieldname}
		for field in frappe.get_meta(doctype).fields
		if field.fieldtype not in no_value_fields and field.label and field.fieldname
	]
	standard_fields = [
		{"label": "Name", "fieldname": "name"},
		{"label": "Created On", "fieldname": "creation"},
		{"label": "Last Modified", "fieldname": "modified"},
		{"label": "Modified By", "fieldname": "modified_by"},
		{"label": "Owner", "fieldname": "owner"},
	]
	for field in standard_fields:
		fields.append(
			{"label": _(field["label"]), "fieldname": field["fieldname"], "value": field["fieldname"]}
		)
	return fields


@frappe.whitelist(methods=["GET"])
def get_filter_fields(doctype: str) -> list[dict]:
	"""Return the fields a doctype's list can be filtered by.

	doctype: the DocType.
	"""
	controller = get_controller(doctype)
	restricted_fields = []
	if hasattr(controller, "get_non_filterable_fields"):
		restricted_fields = controller.get_non_filterable_fields()

	# Link fields to nested set doctypes can use the "descendants of" operators;
	# found the same way frappe's boot builds `nested_set_doctypes`
	tree_doctypes = set(frappe.get_all("DocField", {"fieldname": "lft"}, pluck="parent"))

	fields = []
	for field in get_standard_filter_fields(doctype) + frappe.get_meta(doctype).as_dict().get("fields", []):
		if field.get("fieldname") in restricted_fields or field.get("fieldtype") not in FILTER_FIELDTYPES:
			continue
		field["name"] = field.get("fieldname")
		field["label"] = _(field.get("label"))
		field["value"] = field.get("fieldname")
		field["is_tree"] = field.get("fieldtype") == "Link" and field.get("options") in tree_doctypes
		fields.append(field)
	return fields


@frappe.whitelist(methods=["GET"])
def get_group_by_fields(doctype: str) -> list[dict]:
	"""Return the fields a doctype's list can be grouped by.

	doctype: the DocType.
	"""
	fields = [
		{"label": _(field.label), "fieldname": field.fieldname}
		for field in frappe.get_meta(doctype).fields
		if field.fieldtype in GROUP_BY_FIELDTYPES and field.label and field.fieldname
	]
	standard_fields = [
		{"label": "Name", "fieldname": "name"},
		{"label": "Created On", "fieldname": "creation"},
		{"label": "Last Modified", "fieldname": "modified"},
		{"label": "Modified By", "fieldname": "modified_by"},
		{"label": "Owner", "fieldname": "owner"},
		{"label": "Like", "fieldname": "_liked_by"},
		{"label": "Assigned To", "fieldname": "_assign"},
		{"label": "Comments", "fieldname": "_comments"},
		{"label": "Created On", "fieldname": "creation"},
		{"label": "Modified On", "fieldname": "modified"},
	]
	for field in standard_fields:
		fields.append({"label": _(field["label"]), "fieldname": field["fieldname"]})
	return fields


@frappe.whitelist(methods=["GET"])
def get_quick_filters(doctype: str, cached: bool = True) -> list[dict]:
	"""Return the quick filters shown above a doctype's list.

	doctype: the DocType.
	cached: read the doctype's cached meta.
	"""
	meta = frappe.get_meta(doctype, cached)
	fieldnames = get_quick_filter_fieldnames(doctype)
	if fieldnames is None:
		fields = [field for field in meta.fields if field.in_standard_filter]
	else:
		fields = [NAME_QUICK_FILTER if name == "name" else meta.get_field(name) for name in fieldnames]

	quick_filters = [get_quick_filter(field) for field in fields if field]
	if doctype == "CRM Lead":
		quick_filters = [f for f in quick_filters if f.get("fieldname") != "converted"]
	return quick_filters


@frappe.whitelist(methods=["POST"])
def set_quick_filters(doctype: str, fieldnames: list[str]) -> None:
	"""Set the quick filters shown above a doctype's list, for every user.

	doctype: the DocType.
	fieldnames: the fields to show as quick filters, in order.
	"""
	frappe.only_for(("System Manager", "Sales Manager"))
	old_fieldnames = get_quick_filter_fieldnames(doctype)
	if old_fieldnames is None:
		old_fieldnames = [f.fieldname for f in frappe.get_meta(doctype).fields if f.in_standard_filter]

	save_quick_filter_fieldnames(doctype, fieldnames)
	for fieldname in old_fieldnames:
		if fieldname not in fieldnames:
			set_in_standard_filter(doctype, fieldname, 0)
	for fieldname in fieldnames:
		if fieldname not in old_fieldnames:
			set_in_standard_filter(doctype, fieldname, 1)


@frappe.whitelist(methods=["GET"])
def get_column_fields(doctype: str) -> list[dict]:
	"""Return the fields a doctype's list can show as columns.

	doctype: the DocType.
	"""
	fields = [
		{
			"label": _(field.label),
			"fieldtype": field.fieldtype,
			"fieldname": field.fieldname,
			"options": field.options,
		}
		for field in frappe.get_meta(doctype).fields
		if field.fieldtype not in no_value_fields and field.label and field.fieldname
	]
	for field in STANDARD_COLUMN_FIELDS:
		if field not in fields:
			fields.append({**field, "label": _(field["label"])})
	return fields


@frappe.whitelist(methods=["GET"])
def get_views(doctype: str) -> list[dict]:
	"""Return the saved list views of a doctype that the user can see.

	doctype: the DocType.
	"""
	View = frappe.qb.DocType("CRM View Settings")
	return (
		frappe.qb.from_(View)
		.select("*")
		.where(Criterion.any([View.user == "", View.user == frappe.session.user]))
		.where(View.dt == doctype)
		.run(as_dict=True)
	)


@frappe.whitelist(methods=["GET"])
def get_list_scripts(doctype: str) -> dict:
	"""Return a doctype's enabled CRM Form Scripts for its form and its list.

	doctype: the DocType.
	"""
	return {"form_script": get_form_script(doctype), "list_script": get_form_script(doctype, "List")}


def get_saved_view(doctype, name):
	"""The parsed settings of a saved view the user can see; empty when no name is given."""
	if not name:
		return frappe._dict()

	view = frappe.get_doc("CRM View Settings", name)
	if view.dt != doctype or view.user not in ("", None, frappe.session.user):
		raise frappe.PermissionError(_("View {0} is not a view of {1}").format(name, doctype))

	columns, rows = (None, None) if view.load_default_columns else (view.columns, view.rows)
	return frappe._dict(
		type=view.type,
		filters=frappe.parse_json(view.filters or "null"),
		order_by=view.order_by,
		group_by_field=view.group_by_field,
		columns=frappe.parse_json(columns or "null"),
		rows=frappe.parse_json(rows or "null"),
		column_field=view.column_field,
		title_field=view.title_field,
		kanban_columns=frappe.parse_json(view.kanban_columns or "null"),
		kanban_fields=frappe.parse_json(view.kanban_fields or "null"),
	)


def get_lean_kanban_column(column):
	kanban_column = column["column"]
	return {
		"name": kanban_column.get("name"),
		"count": kanban_column.get("count"),
		"total": kanban_column.get("all_count"),
		"records": column["data"],
	}


def get_standard_filter_fields(doctype):
	return [
		{"fieldname": "name", "fieldtype": "Link", "label": "Name", "options": doctype},
		{"fieldname": "owner", "fieldtype": "Link", "label": "Created By", "options": "User"},
		{"fieldname": "modified_by", "fieldtype": "Link", "label": "Last Updated By", "options": "User"},
		{"fieldname": "_user_tags", "fieldtype": "Data", "label": "Tags"},
		{"fieldname": "_liked_by", "fieldtype": "Data", "label": "Like"},
		{"fieldname": "_comments", "fieldtype": "Text", "label": "Comments"},
		{"fieldname": "_assign", "fieldtype": "Text", "label": "Assigned To"},
		{"fieldname": "creation", "fieldtype": "Datetime", "label": "Created On"},
		{"fieldname": "modified", "fieldtype": "Datetime", "label": "Last Updated On"},
	]


def get_quick_filter(field):
	options = field.get("options")
	if field.get("fieldtype") == "Select" and options and isinstance(options, str):
		options = [{"label": option, "value": option} for option in options.split("\n")]
		if all(option.get("value") for option in options):
			options.insert(0, {"label": "", "value": ""})
	return {
		"label": _(field.get("label")),
		"fieldname": field.get("fieldname"),
		"fieldtype": field.get("fieldtype"),
		"options": options,
	}


def get_quick_filter_fieldnames(doctype):
	"""The fieldnames saved in CRM Global Settings, or None when the doctype uses its standard filters."""
	settings = frappe.db.exists("CRM Global Settings", {"dt": doctype, "type": "Quick Filters"})
	if settings:
		return frappe.parse_json(frappe.db.get_value("CRM Global Settings", settings, "json")) or []


def save_quick_filter_fieldnames(doctype, fieldnames):
	if settings := frappe.db.exists("CRM Global Settings", {"dt": doctype, "type": "Quick Filters"}):
		frappe.db.set_value("CRM Global Settings", settings, "json", json.dumps(fieldnames))
		return
	frappe.get_doc(
		doctype="CRM Global Settings", dt=doctype, type="Quick Filters", json=json.dumps(fieldnames)
	).insert()


def set_in_standard_filter(doctype, fieldname, value):
	filters = {"doc_type": doctype, "field_name": fieldname, "property": "in_standard_filter"}
	if property_setter := frappe.db.exists("Property Setter", filters):
		frappe.db.set_value("Property Setter", property_setter, "value", value)
		return
	make_property_setter(
		doctype, fieldname, "in_standard_filter", value, "Check", validate_fields_for_doctype=False
	)


NAME_QUICK_FILTER = {"label": "Name", "fieldname": "name", "fieldtype": "Data"}
FILTER_FIELDTYPES = (
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
	"Rating",
	"Date",
	"Datetime",
)
GROUP_BY_FIELDTYPES = (
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
)
STANDARD_COLUMN_FIELDS = (
	{"label": "Name", "fieldtype": "Data", "fieldname": "name"},
	{"label": "Created On", "fieldtype": "Datetime", "fieldname": "creation"},
	{"label": "Last Modified", "fieldtype": "Datetime", "fieldname": "modified"},
	{"label": "Modified By", "fieldtype": "Link", "fieldname": "modified_by", "options": "User"},
	{"label": "Assigned To", "fieldtype": "Text", "fieldname": "_assign"},
	{"label": "Owner", "fieldtype": "Link", "fieldname": "owner", "options": "User"},
	{"label": "Like", "fieldname": "_liked_by", "fieldtype": "Data"},
)
