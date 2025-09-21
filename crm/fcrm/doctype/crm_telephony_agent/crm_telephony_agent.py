# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMTelephonyAgent(Document):
	def validate(self):
		self.set_primary()

	def set_primary(self):
		# Used to set primary mobile no.
		if len(self.phone_nos) == 0:
			self.mobile_no = ""
			return

		is_primary = [phone.number for phone in self.phone_nos if phone.get("is_primary")]

		if len(is_primary) > 1:
			frappe.throw(
				_("Only one {0} can be set as primary.").format(frappe.bold(frappe.unscrub("mobile_no")))
			)

		primary_number_exists = False
		for d in self.phone_nos:
			if d.get("is_primary") == 1:
				primary_number_exists = True
				self.mobile_no = d.number
				break

		if not primary_number_exists:
			self.mobile_no = ""
