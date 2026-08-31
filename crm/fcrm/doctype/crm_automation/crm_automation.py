# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.model.document import Document

from crm.automation.engine import compile_steps, parse_json, validate_steps


class CRMAutomation(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		allow_reenrollment: DF.Check
		compiled_steps: DF.JSON | None
		description: DF.SmallText | None
		enabled: DF.Check
		exit_on_reply: DF.Check
		steps: DF.JSON
		time_window_enabled: DF.Check
		title: DF.Data
		trigger_condition: DF.JSON | None
		trigger_config: DF.JSON | None
		trigger_event: DF.Literal[
			"Lead Created",
			"Deal Created",
			"Lead Status Changed",
			"Deal Status Changed",
			"Booking Created",
			"Booking Cancelled",
			"Booking No Show",
			"Booking Completed",
			"Incoming SMS",
			"Customer Replied",
			"Email Opened",
			"Trigger Link Clicked",
			"Tag Added",
			"Tag Removed",
			"Task Completed",
			"Note Added",
			"Date Reminder",
			"Inbound Webhook",
		]
		webhook_key: DF.Data | None
		window_days: DF.JSON | None
		window_end: DF.Time | None
		window_start: DF.Time | None
	# end: auto-generated types

	def validate(self):
		steps = parse_json(self.steps)
		validate_steps(steps)
		self.compiled_steps = json.dumps(compile_steps(steps))
		if self.trigger_event == "Inbound Webhook" and not self.webhook_key:
			self.webhook_key = frappe.generate_hash(length=32)

	def on_trash(self):
		frappe.db.delete("CRM Automation Enrollment", {"automation": self.name})
