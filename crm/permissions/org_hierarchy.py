# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.caching import request_cache

_OWNER_FIELD = {
	"CRM Lead": "lead_owner",
	"CRM Deal": "deal_owner",
}


def hierarchy_enabled() -> bool:
	return bool(frappe.db.get_single_value("FCRM Settings", "enable_sales_hierarchy"))


# ptypes a non-Sales Manager "view all" role may exercise on records it does not own
_VIEW_ALL_PTYPES = ("read", "select")


def _view_all_roles(roles) -> set[str]:
	"""Roles of the user that FCRM Settings > "Roles that see all Leads and Deals" lists."""
	settings = frappe.get_cached_doc("FCRM Settings")  # invalidated on save
	return {d.role for d in settings.view_all_roles}.intersection(roles)


def _permission_query_conditions(user: str | None, doctype: str):
	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return ""

	roles = frappe.get_roles(user)
	if "System Manager" in roles:
		return ""

	in_tree = hierarchy_enabled() and _in_hierarchy(user)

	# A view-all role outside the tree sees everything (Sales Manager by default)
	if _view_all_roles(roles) and not in_tree:
		return ""

	owner_field = _OWNER_FIELD[doctype]
	DT = frappe.qb.DocType(doctype)
	Todo = frappe.qb.DocType("ToDo").as_("_todo")

	if in_tree:
		# Owner is the user themselves or any member of their subtree
		q1 = (DT[owner_field] == user) | DT[owner_field].isin(_team_mem_query(user))
		# Assigned to the user or any member of their subtree by ToDo
		q2 = DT.name.isin(
			frappe.qb.from_(Todo)
			.select(Todo.reference_name)
			.where(
				(Todo.reference_type == doctype)
				& (Todo.status != "Cancelled")
				& ((Todo.allocated_to == user) | (Todo.allocated_to.isin(_team_mem_query(user))))
			)
		)
		return q1 | q2

	# Sales User default: own records and records directly assigned to them
	q1 = DT[owner_field] == user
	q2 = DT.name.isin(
		frappe.qb.from_(Todo)
		.select(Todo.reference_name)
		.where((Todo.reference_type == doctype) & (Todo.status != "Cancelled") & (Todo.allocated_to == user))
	)
	return q1 | q2


def get_lead_permission_query_conditions(user=None):
	cond = _permission_query_conditions(user, "CRM Lead")
	return cond.get_sql(with_namespace=True, quote_char="`", secondary_quote_char="'") if cond else ""


def get_deal_permission_query_conditions(user=None):
	cond = _permission_query_conditions(user, "CRM Deal")
	return cond.get_sql(with_namespace=True, quote_char="`", secondary_quote_char="'") if cond else ""


def _has_permission(doc, ptype, user, doctype: str) -> bool | None:
	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return True

	roles = frappe.get_roles(user)
	if "System Manager" in roles:
		return True

	if ptype == "create" or not doc.name:
		return True

	in_tree = hierarchy_enabled() and _in_hierarchy(user)
	view_all = _view_all_roles(roles)
	if view_all and not in_tree:
		# Sales Manager keeps its historical bypass for every ptype. Any other
		# role listed in the setting only lifts the row filter for read/select;
		# writes still need ownership or assignment (plus DocPerm).
		if "Sales Manager" in view_all or ptype in _VIEW_ALL_PTYPES:
			return True

	conditions = _permission_query_conditions(user, doctype)
	DT = frappe.qb.DocType(doctype)
	return bool(
		frappe.qb.from_(DT).select(DT.name).where(DT.name == doc.name).where(conditions).limit(1).run()
	)


def has_lead_permission(doc, ptype, user):
	return _has_permission(doc, ptype, user, "CRM Lead")


def has_deal_permission(doc, ptype, user):
	return _has_permission(doc, ptype, user, "CRM Deal")


def _in_hierarchy(user: str) -> bool:
	return bool(frappe.db.exists("CRM Sales Hierarchy", {"user": user}))


def _team_mem_query(user: str):
	Mgr = frappe.qb.DocType("CRM Sales Hierarchy").as_("_sqmgr")
	Member = frappe.qb.DocType("CRM Sales Hierarchy").as_("_sqmem")
	return (
		frappe.qb.from_(Mgr)
		.join(Member)
		.on((Member.lft >= Mgr.lft) & (Member.lft <= Mgr.rgt))
		.select(Member.user)
		.where(Mgr.user == user)
	)
