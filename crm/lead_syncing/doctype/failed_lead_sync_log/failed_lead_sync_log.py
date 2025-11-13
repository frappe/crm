# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class FailedLeadSyncLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		lead_data: DF.Code | None
		source: DF.Link | None
		traceback: DF.Code | None
		type: DF.Literal["Duplicate", "Failure"]
	# end: auto-generated types

	pass
