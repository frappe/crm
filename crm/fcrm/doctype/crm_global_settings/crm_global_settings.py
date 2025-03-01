# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from crm.api.doc import clear_quick_filters_cache


class CRMGlobalSettings(Document):
	def after_save(self):
		if self.type == "Quick Filters":
			clear_quick_filters_cache(self.dt)
