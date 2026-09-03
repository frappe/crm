# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FailedLeadSyncLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		lead_data: DF.Code | None
		form: DF.Link | None
		traceback: DF.Code | None
		type: DF.Literal["Duplicate", "Failure", "Synced"]
	# end: auto-generated types

	@frappe.whitelist()
	def retry_sync(self):
		"""Re-import this lead through the Meta engine."""
		from crm.integrations.meta.leads import store_lead

		lead_data = frappe.parse_json(self.lead_data)
		form_id = self.form or lead_data.get("form_id")
		if not form_id:
			frappe.throw(frappe._("This log has no form to retry against"))

		result = store_lead(lead_data, form_id)
		if result == "failed":
			frappe.throw(frappe._("The lead could not be imported, see the newest log"))
		self.type = "Synced"
		self.save()
		return result
