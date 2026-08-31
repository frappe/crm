# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, validate_email_address


class CRMBooking(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		access_token: DF.Data | None
		agent: DF.Link
		calendar: DF.Link
		ends_on: DF.Datetime
		invitee_email: DF.Data
		invitee_name: DF.Data
		invitee_phone: DF.Data | None
		invitee_timezone: DF.Data | None
		lead: DF.Link | None
		notes: DF.SmallText | None
		starts_on: DF.Datetime
		status: DF.Literal["Confirmed", "Cancelled", "Completed", "No Show"]
	# end: auto-generated types

	def before_insert(self):
		if not self.access_token:
			self.access_token = frappe.generate_hash(length=32)

	def validate(self):
		validate_email_address(self.invitee_email, throw=True)
		if get_datetime(self.ends_on) <= get_datetime(self.starts_on):
			frappe.throw(_("End time must be after start time"))
