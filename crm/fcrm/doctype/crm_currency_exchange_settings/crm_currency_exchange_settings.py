# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe import _
from frappe.model.document import Document


class CRMCurrencyExchangeSettings(Document):
	pass


def get_exchange_rate(from_currency, to_currency, date=None):
	if not date:
		date = "latest"

	api_endpoint = f"https://api.frankfurter.app/{date}?from={from_currency}&to={to_currency}"
	res = requests.get(api_endpoint, timeout=5)
	if res.ok:
		data = res.json()
		return data["rates"][to_currency]

	# Fallback to exchangerate.host if Frankfurter API fails
	ces = frappe.get_single("CRM Currency Exchange Settings")
	if ces and ces.service_provider == "exchangerate.host":
		if not ces.access_key:
			frappe.throw(
				_("Access Key is required for Service Provider: {0}").format(
					frappe.bold(ces.service_provider)
				)
			)

		params = {
			"access_key": ces.access_key,
			"from": from_currency,
			"to": to_currency,
			"amount": 1,
		}

		if date != "latest":
			params["date"] = date

		api_endpoint = "https://api.exchangerate.host/convert"

		res = requests.get(api_endpoint, params=params, timeout=5)
		if res.ok:
			data = res.json()
			return data["result"]

	frappe.log_error(
		title="Exchange Rate Fetch Error",
		message=f"Failed to fetch exchange rate from {from_currency} to {to_currency} on {date}",
	)
	return 1.0  # Default exchange rate if API call fails or no rate found
