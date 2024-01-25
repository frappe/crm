# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMOrganization(Document):
		def on_update(self):
			self.update_deal_organization_fields()

		def update_deal_organization_fields(self):
			if (
				self.has_value_changed("website")
				or self.has_value_changed("territory")
				or self.has_value_changed("annual_revenue")
			):
				for deal in frappe.get_all(
					"CRM Deal",
					filters={"organization": self.name},
				):
					if self.has_value_changed("website"):
						frappe.db.set_value("CRM Deal", deal.name, "website", self.website)
					if self.has_value_changed("territory"):
						frappe.db.set_value("CRM Deal", deal.name, "territory", self.territory)
					if self.has_value_changed("annual_revenue"):
						frappe.db.set_value("CRM Deal", deal.name, "annual_revenue", self.annual_revenue)

		@staticmethod
		def default_list_data():
			columns = [
				{
					'label': 'Organization',
					'type': 'Data',
					'key': 'organization_name',
					'width': '16rem',
				},
				{
					'label': 'Website',
					'type': 'Data',
					'key': 'website',
					'width': '14rem',
				},
				{
					'label': 'Industry',
					'type': 'Link',
					'key': 'industry',
					'options': 'CRM Industry',
					'width': '14rem',
				},
				{
					'label': 'Annual Revenue',
					'type': 'Currency',
					'key': 'annual_revenue',
					'width': '14rem',
				},
				{
					'label': 'Last Modified',
					'type': 'Datetime',
					'key': 'modified',
					'width': '8rem',
				},
			]
			rows = [
				"name",
				"organization_name",
				"organization_logo",
				"website",
				"industry",
				"annual_revenue",
				"modified",
			]
			return {'columns': columns, 'rows': rows}
