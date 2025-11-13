# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class FacebookLeadFormQuestion(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		id: DF.Data | None
		key: DF.Data
		label: DF.Data | None
		mapped_to_crm_field: DF.Autocomplete | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		type: DF.Data | None
	# end: auto-generated types

	pass
