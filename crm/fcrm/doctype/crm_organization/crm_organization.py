# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMOrganization(Document):
	def validate(self):
		self.update_currency_exchange()

	def update_currency_exchange(self):
		if self.has_value_changed("currency") or not self.currency_exchange:
			system_currency = frappe.db.get_single_value("System Settings", "currency")
			currency_exchange = None
			if self.currency and self.currency != system_currency:
				if not frappe.db.exists(
					"CRM Currency Exchange", {"from_currency": self.currency, "to_currency": system_currency}
				):
					new_er = frappe.new_doc("CRM Currency Exchange")
					new_er.from_currency = self.currency
					new_er.to_currency = system_currency
					new_er.insert(ignore_permissions=True)
					currency_exchange = new_er.name
				else:
					currency_exchange = frappe.db.get_value(
						"CRM Currency Exchange",
						{"from_currency": self.currency, "to_currency": system_currency},
						"name",
					)

			currency_exchange and self.db_set("currency_exchange", currency_exchange)

	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Organization",
				"type": "Data",
				"key": "organization_name",
				"width": "16rem",
			},
			{
				"label": "Website",
				"type": "Data",
				"key": "website",
				"width": "14rem",
			},
			{
				"label": "Industry",
				"type": "Link",
				"key": "industry",
				"options": "CRM Industry",
				"width": "14rem",
			},
			{
				"label": "Annual Revenue",
				"type": "Currency",
				"key": "annual_revenue",
				"width": "14rem",
			},
			{
				"label": "Last Modified",
				"type": "Datetime",
				"key": "modified",
				"width": "8rem",
			},
		]
		rows = [
			"name",
			"organization_name",
			"organization_logo",
			"website",
			"industry",
			"currency",
			"annual_revenue",
			"modified",
		]
		return {"columns": columns, "rows": rows}
