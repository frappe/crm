# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from functools import cached_property

import frappe
from pypika.terms import EmptyCriterion

from crm.permissions.org_hierarchy import permission_query_conditions, team_members_query

SALES_ROLES = ("Sales User", "Sales Manager")


class Mine:
	"""Every CRM permission rule lets a user read their own and assigned records, so no condition is needed."""

	def __init__(self, user: str):
		self.user = user

	def records(self, doctype: str, table, owner_field: str):
		return table._assign.like(f'%"{self.user}"%') | (table[owner_field] == self.user)

	def tasks(self, task):
		return task.assigned_to == self.user


class Team:
	"""CRM Task has no permission hook, so tasks are scoped to the team's members instead."""

	def __init__(self, user: str):
		self.user = user
		self.sees_everyone = not permission_query_conditions(user, "CRM Lead")
		self.key = "all" if self.sees_everyone else user

	def records(self, doctype: str, table, owner_field: str):
		return permission_query_conditions(self.user, doctype) or EmptyCriterion()

	def tasks(self, task):
		return task.assigned_to.isin(self.members or [None])

	@cached_property
	def members(self) -> list:
		if self.sees_everyone:
			return sales_users()
		return team_members_query(self.user).run(pluck=True)


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
