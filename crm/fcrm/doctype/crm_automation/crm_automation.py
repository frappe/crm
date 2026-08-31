# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from crm.automation.engine import parse_json, validate_steps


class CRMAutomation(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		allow_reenrollment: DF.Check
		description: DF.SmallText | None
		enabled: DF.Check
		exit_on_reply: DF.Check
		steps: DF.JSON
		title: DF.Data
		trigger_condition: DF.JSON | None
		trigger_event: DF.Literal[
			"Lead Created",
			"Deal Created",
			"Lead Status Changed",
			"Deal Status Changed",
			"Booking Created",
			"Booking Cancelled",
			"Incoming SMS",
		]
	# end: auto-generated types

	def validate(self):
		validate_steps(parse_json(self.steps))

	def on_trash(self):
		frappe.db.delete("CRM Automation Enrollment", {"automation": self.name})
