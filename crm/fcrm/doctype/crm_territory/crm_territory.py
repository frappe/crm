# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils.nestedset import NestedSet


class CRMTerritory(NestedSet):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		is_group: DF.Check
		lft: DF.Int
		old_parent: DF.Link | None
		parent_crm_territory: DF.Link | None
		rgt: DF.Int
		territory_manager: DF.Link | None
		territory_name: DF.Data
	# end: auto-generated types

	nsm_parent_field = "parent_crm_territory"

	def validate(self):
		self.validate_parent_is_group()

	def validate_parent_is_group(self):
		parent = self.parent_crm_territory
		if not parent:
			return

		if parent == self.name:
			frappe.throw(_("Territory cannot be its own parent"))

		if not frappe.db.get_value("CRM Territory", parent, "is_group"):
			frappe.throw(
				_("Parent Territory {0} is not a group. Only group territories can have children.").format(
					frappe.bold(parent)
				)
			)


def on_doctype_update():
	frappe.db.add_index("CRM Territory", ["lft", "rgt"])
