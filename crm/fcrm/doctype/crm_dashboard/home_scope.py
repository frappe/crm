# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Whose leads, deals and tasks a Home widget covers: the viewer's own, or a manager's team."""

from functools import cached_property

import frappe
from pypika.terms import EmptyCriterion

from crm.permissions.org_hierarchy import _permission_query_conditions, _team_mem_query

SALES_ROLES = ("Sales User", "Sales Manager")


class Mine:
	"""Records owned by or assigned to the user. Every CRM permission rule lets a user read
	those, so no permission condition is needed and each query keeps one selective predicate."""

	def __init__(self, user: str):
		self.user = user

	def records(self, doctype: str, table, owner_field: str):
		return table._assign.like(f'%"{self.user}"%') | (table[owner_field] == self.user)

	def tasks(self, task):
		return task.assigned_to == self.user


class Team:
	"""What the manager can see under Sales Hierarchy permissions: their subtree, or everyone.

	CRM Task has no permission hook, so tasks are scoped to the team's members instead.
	"""

	def __init__(self, user: str):
		self.user = user
		self.sees_everyone = not _permission_query_conditions(user, "CRM Lead")
		self.key = "all" if self.sees_everyone else user

	def records(self, doctype: str, table, owner_field: str):
		return _permission_query_conditions(self.user, doctype) or EmptyCriterion()

	def tasks(self, task):
		return task.assigned_to.isin(self.members or [None])

	@cached_property
	def members(self) -> list:
		if self.sees_everyone:
			return sales_users()
		return _team_mem_query(self.user).run(pluck=True)


def sales_users() -> list:
	user = frappe.qb.DocType("User")
	has_role = frappe.qb.DocType("Has Role")
	return (
		frappe.qb.from_(user)
		.join(has_role)
		.on((has_role.parent == user.name) & (has_role.parenttype == "User"))
		.select(user.name)
		.distinct()
		.where((user.enabled == 1) & has_role.role.isin(SALES_ROLES))
		.run(pluck=True)
	)
