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

	api_used = "frankfurter"

	api_endpoint = f"https://api.frankfurter.app/{date}?from={from_currency}&to={to_currency}"
	res = requests.get(api_endpoint, timeout=5)
	if res.ok:
		data = res.json()
		return data["rates"][to_currency]

	# Fallback to exchangerate.host if Frankfurter API fails
	ces = frappe.get_single("CRM Currency Exchange Settings")
	if ces and ces.service_provider == "exchangerate.host":
		api_used = "exchangerate.host"
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
		message=f"Failed to fetch exchange rate from {from_currency} to {to_currency} using {api_used} API.",
	)

	if api_used == "frankfurter":
		user = frappe.session.user
		is_manager = (
			"System Manager" in frappe.get_roles(user)
			or "Sales Manager" in frappe.get_roles(user)
			or user == "Administrator"
		)

		if not is_manager:
			frappe.throw(
				_(
					"Ask your manager to set up the Currency Exchange Provider, as default provider does not support currency conversion for {0} to {1}."
				).format(from_currency, to_currency)
			)
		else:
			frappe.throw(
				_(
					"Setup the Currency Exchange Provider as 'exchangerate.host' in settings, as default provider does not support currency conversion for {0} to {1}."
				).format(from_currency, to_currency)
			)

	frappe.throw(
		_(
			"Failed to fetch exchange rate from {0} to {1} on {2}. Please check your internet connection or try again later."
		).format(from_currency, to_currency, date)
	)
