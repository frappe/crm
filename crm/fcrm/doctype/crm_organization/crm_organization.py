# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CRMOrganization(Document):
		@staticmethod
		def sort_options():
			return [
				{ "label": 'Created', "value": 'creation' },
				{ "label": 'Modified', "value": 'modified' },
				{ "label": 'Name', "value": 'name' },
				{ "label": 'Website', "value": 'website' },
				{ "label": 'Amount', "value": 'annual_revenue' },
				{ "label": 'Industry', "value": 'industry' },
			]

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
					'label': 'Last modified',
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
