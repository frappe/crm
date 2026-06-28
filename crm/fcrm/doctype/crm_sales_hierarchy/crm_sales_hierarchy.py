# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import NestedSet, update_nsm


class CRMSalesHierarchy(NestedSet):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		enabled: DF.Check
		full_name: DF.Data | None
		is_group: DF.Check
		lft: DF.Int
		old_parent: DF.Link | None
		reports_to: DF.Link | None
		rgt: DF.Int
		user: DF.Link | None
	# end: auto-generated types

	nsm_parent_field = "reports_to"

	def on_update(self):
		update_nsm(self)
		frappe.cache.delete_value("crm_sales_hierarchy_subtree")

	def validate(self):
		if self.user:
			# Ensure the same user is not mapped to two different nodes
			existing = frappe.db.get_value(
				"CRM Sales Hierarchy",
				{"user": self.user, "name": ["!=", self.name]},
				"name",
			)
			if existing:
				frappe.throw(
					frappe._("User {0} is already mapped to hierarchy node {1}.").format(self.user, existing)
				)

		# A node with reports_to becomes a child so its parent must be a group
		if self.reports_to and not frappe.db.get_value("CRM Sales Hierarchy", self.reports_to, "is_group"):
			frappe.db.set_value("CRM Sales Hierarchy", self.reports_to, "is_group", 1)

	def on_trash(self):
		frappe.cache.delete_value("crm_sales_hierarchy_subtree")


def on_doctype_update():
	frappe.db.add_index("CRM Sales Hierarchy", ["lft", "rgt"])
	frappe.db.add_index("CRM Sales Hierarchy", ["user"])
