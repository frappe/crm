# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMWebFormField(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		field_description: DF.SmallText | None
		fieldname: DF.Data
		fieldtype: DF.Data | None
		label: DF.Data | None
		options: DF.SmallText | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		placeholder: DF.Data | None
		reqd: DF.Check
	# end: auto-generated types

	pass
