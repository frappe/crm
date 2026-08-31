# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMDialSessionEntry(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		disposition: DF.Literal[
			"", "Interested", "Not Interested", "No Answer", "Callback", "Voicemail", "Wrong Number"
		]
		display_name: DF.Data | None
		note: DF.SmallText | None
		number: DF.Data
		reference_doctype: DF.Link
		reference_name: DF.DynamicLink
		status: DF.Literal["Pending", "Done", "Skipped"]
	# end: auto-generated types

	pass
