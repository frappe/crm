# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMAutomationStepLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		action: DF.Data | None
		detail: DF.SmallText | None
		status: DF.Literal["Success", "Failed", "Skipped"]
		step_index: DF.Int
	# end: auto-generated types

	pass
