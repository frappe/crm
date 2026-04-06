# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from crm.lead_syncing.doctype.lead_sync_source.facebook import FacebookSyncSource


class FailedLeadSyncLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		lead_data: DF.Code | None
		source: DF.Link | None
		traceback: DF.Code | None
		type: DF.Literal["Duplicate", "Failure", "Synced"]
	# end: auto-generated types

	@frappe.whitelist()
	def retry_sync(self):
		if not self.source:
			frappe.throw(frappe._("Can't retry sync for this without source!"))

		source = frappe.get_cached_doc("Lead Sync Source", self.source)
		if source.type != "Facebook":
			frappe.throw(frappe._("Not implemented yet!"))

		crm_lead = FacebookSyncSource(
			source.get_password("access_token"), source.facebook_lead_form
		).sync_single_lead(frappe.parse_json(self.lead_data), raise_exception=True)

		self.type = "Synced"
		self.save()
		return crm_lead
