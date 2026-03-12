# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMTelephonyAgent(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.fcrm.doctype.crm_telephony_phone.crm_telephony_phone import CRMTelephonyPhone

		call_receiving_device: DF.Literal["Computer", "Phone"]
		default_medium: DF.Literal["", "Twilio", "Exotel"]
		exotel_number: DF.Data | None
		mobile_no: DF.Data | None
		phone_nos: DF.Table[CRMTelephonyPhone]
		twilio_number: DF.Data | None
		user: DF.Link
		user_name: DF.Data | None
	# end: auto-generated types

	def validate(self):
		self.update_phone_nos_based_on_mobile_no()
		self.set_primary()

	def update_phone_nos_based_on_mobile_no(self):
		if not self.get_doc_before_save():
			return

		old_mobile_no = self.get_doc_before_save().mobile_no
		new_mobile_no = self.mobile_no

		if old_mobile_no != new_mobile_no:
			# if new mobile no. is not in phone_nos table, then add it
			if new_mobile_no and not any(phone.get("number") == new_mobile_no for phone in self.phone_nos):
				self.append("phone_nos", {"number": new_mobile_no, "is_primary": 1})

			# if old mobile no. is in phone_nos table, then remove it
			for phone in self.phone_nos:
				if phone.get("number") == old_mobile_no:
					self.phone_nos.remove(phone)
					break

	def set_primary(self):
		# Used to set primary mobile no.
		if len(self.phone_nos) == 0 and not self.mobile_no:
			return
		elif len(self.phone_nos) == 0 and self.mobile_no:
			self.append("phone_nos", {"number": self.mobile_no, "is_primary": 1})

		is_primary = [phone.get("number") for phone in self.phone_nos if phone.get("is_primary")]

		if len(is_primary) > 1:
			frappe.throw(
				_("Only one {0} can be set as primary.").format(frappe.bold(frappe.unscrub("mobile_no")))
			)

		primary_number_exists = False
		for d in self.phone_nos:
			if d.get("is_primary") == 1:
				primary_number_exists = True
				self.mobile_no = d.get("number")
				break

		if not primary_number_exists:
			self.mobile_no = ""
