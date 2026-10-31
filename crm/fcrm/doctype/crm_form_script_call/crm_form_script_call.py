# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMFormScriptCall(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		catalog_key: DF.Data | None
		gap: DF.SmallText | None
		line: DF.Int
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		v1_call: DF.SmallText | None
		verb: DF.Data | None
	# end: auto-generated types

	pass
