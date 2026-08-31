# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMAutomationEnrollment(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.fcrm.doctype.crm_automation_step_log.crm_automation_step_log import (
			CRMAutomationStepLog,
		)

		automation: DF.Link
		current_step: DF.Int
		logs: DF.Table[CRMAutomationStepLog]
		reference_doctype: DF.Link
		reference_name: DF.DynamicLink
		status: DF.Literal["Active", "Waiting", "Completed", "Exited", "Failed"]
		wait_until: DF.Datetime | None
	# end: auto-generated types

	pass
