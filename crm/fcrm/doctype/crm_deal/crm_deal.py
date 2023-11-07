# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CRMDeal(Document):
	@staticmethod
	def sort_options():
		return [
			{ "label": 'Created', "value": 'creation' },
			{ "label": 'Modified', "value": 'modified' },
			{ "label": 'Status', "value": 'status' },
			{ "label": 'Deal owner', "value": 'deal_owner' },
			{ "label": 'Organization', "value": 'organization' },
			{ "label": 'Email', "value": 'email' },
			{ "label": 'Mobile no', "value": 'mobile_no' },
		]
