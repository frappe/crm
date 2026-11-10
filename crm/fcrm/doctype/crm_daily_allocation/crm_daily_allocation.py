# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMDailyAllocation(Document):
	def validate(self):
		if not self.allocated_by:
			self.allocated_by = frappe.session.user
		if not self.allocation_date:
			self.allocation_date = frappe.utils.today()
		if not self.status:
			self.status = "To Do"

