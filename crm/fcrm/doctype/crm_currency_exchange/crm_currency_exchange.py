# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import frappe
import requests
from frappe import _
from frappe.model.document import Document


class CRMCurrencyExchange(Document):
	def validate(self):
		if self.exchange_rate and self.exchange_rate <= 0:
			frappe.throw(_("Exchange Rate must be a positive number."))

		if self.from_currency == self.to_currency:
			frappe.throw(_("From Currency and To Currency cannot be the same."))

	def on_update(self):
		if not self.exchange_rate:
			self.update_exchange_rate()

		if self.exchange_rate <= 0:
			frappe.throw(_("Exchange Rate must be a positive number."))

	@frappe.whitelist()
	def update_exchange_rate(self):
		exchange_rate = get_exchange_rate(self.from_currency, self.to_currency)
		self.db_set("exchange_rate", exchange_rate)
		return exchange_rate


def get_exchange_rate(from_currency, to_currency):
	url = f"https://api.frankfurter.app/latest?from={from_currency}&to={to_currency}"
	response = requests.get(url)

	if response.status_code == 200:
		data = response.json()
		rate = data["rates"].get(to_currency)
		return rate
	else:
		frappe.throw(_("Failed to fetch exchange rate from external API. Please try again later."))
		return None
