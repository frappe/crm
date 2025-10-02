# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from crm.lead_syncing.doctype.lead_sync_source.facebook import sync_leads_from_facebook


class LeadSyncSource(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		access_token: DF.Password | None
		enabled: DF.Check
		facebook_lead_form: DF.Link | None
		facebook_page: DF.Link | None
		last_synced_at: DF.Datetime | None
		type: DF.Literal["Facebook"]
	# end: auto-generated types

	def before_save(self):
		if self.type == "Facebook" and self.access_token:
			# fetch_and_store_pages_from_facebook(self.access_token)
			pass

	@frappe.whitelist()
	def sync_leads(self):
		if self.type == "Facebook" and self.access_token:
			if not self.facebook_lead_form:
				frappe.throw(frappe._("Please select a lead gen form before syncing!"))
			sync_leads_from_facebook(self.get_password("access_token"), self.facebook_lead_form)
