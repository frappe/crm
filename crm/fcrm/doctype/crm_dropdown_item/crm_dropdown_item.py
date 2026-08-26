# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CRMDropdownItem(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		hidden: DF.Check
		icon: DF.Code | None
		is_standard: DF.Check
		label: DF.Data | None
		name1: DF.Data | None
		open_in_new_window: DF.Check
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		route: DF.Data | None
		type: DF.Literal["Route", "Separator"]
	# end: auto-generated types

	pass
