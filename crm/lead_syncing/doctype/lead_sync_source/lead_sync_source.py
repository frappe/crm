# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from crm.lead_syncing.doctype.lead_sync_source.facebook import (
	FacebookSyncSource,
	fetch_and_store_pages_from_facebook,
)


class LeadSyncSource(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		access_token: DF.Password
		background_sync_frequency: DF.Literal["Every 5 Minutes", "Every 10 Minutes", "Every 15 Minutes", "Hourly", "Daily", "Monthly"]
		enabled: DF.Check
		facebook_lead_form: DF.Link | None
		facebook_page: DF.Link | None
		last_synced_at: DF.Datetime | None
		type: DF.Literal["Facebook"]
	# end: auto-generated types

	def validate(self):
		self.validate_same_fb_form_active()

	def validate_same_fb_form_active(self):
		if not self.enabled:
			return

		if not self.facebook_lead_form:
			return

		already_active = frappe.db.exists(
			"Lead Sync Source",
			{"enabled": 1, "facebook_lead_form": self.facebook_lead_form, "name": ["!=", self.name]},
		)

		if already_active:
			frappe.throw(frappe._("A lead sync source is already enabled for this Facebook Lead Form!"))

	def before_insert(self):
		if self.type == "Facebook" and self.access_token:
			fetch_and_store_pages_from_facebook(self.access_token)
		# rest of the source types can be added here

	@frappe.whitelist()
	def sync_leads(self):
		if frappe.conf.developer_mode:
			self._sync_leads()
			return

		frappe.enqueue_doc(self.doctype, self.name, "_sync_leads", queue="long")

	def _sync_leads(self):
		if self.type == "Facebook" and self.access_token:
			if not self.facebook_lead_form:
				frappe.throw(frappe._("Please select a lead gen form before syncing!"))

			FacebookSyncSource(
				self.get_password("access_token"),
				self.facebook_lead_form
			).sync()
