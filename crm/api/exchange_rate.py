import frappe
import requests
from frappe import _

from crm.fcrm.doctype.fcrm_settings.fcrm_settings import FCRMSettings


@frappe.whitelist()
def get_exchange_rate(from_currency: str, to_currency: str, date: str | None = None):
	if not date:
		date = "latest"

	# "latest" is keyed by today's date so tomorrow's call automatically misses the cache
	cache_date = frappe.utils.today() if date == "latest" else date
	cache_key = f"exchange_rate_{from_currency}_{to_currency}_{cache_date}"

	cached_rate = frappe.cache().get_value(cache_key)
	if cached_rate is not None:
		return cached_rate

	rate, api_used = _fetch_exchange_rate(from_currency, to_currency, date)

	if rate is not None:
		frappe.cache().set_value(cache_key, rate)
		return rate

	_raise_exchange_rate_error(from_currency, to_currency, date, api_used)


def _fetch_exchange_rate(from_currency: str, to_currency: str, date: str):
	"""Try each configured provider in order and return (rate, provider_name)."""
	settings = frappe.get_single("FCRM Settings")
	provider = settings.service_provider

	_provider = "frankfurter"
	rate = _fetch_from_frankfurter(from_currency, to_currency, date)

	if provider == "frankfurter.app" and rate is not None:
		return rate, provider

	_provider = "fawazahmed-exchange-api"
	rate = _fetch_from_fawaz_api(from_currency, to_currency, date)

	if provider == "fawazahmed-exchange-api" and rate is not None:
		return rate, provider

	if provider == "exchangerate.host":
		return _fetch_from_exchangerate_host(settings, from_currency, to_currency, date), provider

	if provider == "exchangerate-api":
		return _fetch_from_exchangerate_api(settings, from_currency, to_currency), provider

	return rate, _provider


def _fetch_from_frankfurter(from_currency: str, to_currency: str, date: str):
	res = requests.get(f"https://api.frankfurter.app/{date}?from={from_currency}&to={to_currency}", timeout=5)
	if res.ok:
		return res.json()["rates"][to_currency]
	return None


def _fetch_from_fawaz_api(from_currency: str, to_currency: str, date: str):
	from_lower = from_currency.lower()
	to_lower = to_currency.lower()
	date_str = "latest" if date == "latest" else date
	urls = [
		f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{date_str}/v1/currencies/{from_lower}.json",
		f"https://{date_str}.currency-api.pages.dev/v1/currencies/{from_lower}.json",
	]
	for url in urls:
		try:
			res = requests.get(url, timeout=5)
			if res.ok:
				return res.json()[from_lower][to_lower]
		except Exception:
			continue
	return None


def _fetch_from_exchangerate_host(settings: FCRMSettings, from_currency: str, to_currency: str, date: str):
	if not settings.access_key:
		frappe.throw(
			_("Access Key is required for Service Provider: {0}").format(
				frappe.bold(settings.service_provider)
			)
		)
	params = {"access_key": settings.access_key, "from": from_currency, "to": to_currency, "amount": 1}
	if date != "latest":
		params["date"] = date
	res = requests.get("https://api.exchangerate.host/convert", params=params, timeout=5)
	if res.ok:
		return res.json()["result"]
	return None


def _fetch_from_exchangerate_api(settings: FCRMSettings, from_currency: str, to_currency: str):
	if not settings.access_key:
		frappe.throw(
			_("Access Key is required for Service Provider: {0}").format(
				frappe.bold(settings.service_provider)
			)
		)
	res = requests.get(
		f"https://v6.exchangerate-api.com/v6/{settings.access_key}/pair/{from_currency}/{to_currency}",
		timeout=5,
	)
	if res.ok:
		data = res.json()
		if data["result"] == "success":
			return data["conversion_rate"]
	return None


def _raise_exchange_rate_error(from_currency: str, to_currency: str, date: str, api_used: str):
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
					"Ask your manager to set up the Exchange Rate Provider, as default provider does not support currency conversion for {0} to {1}."
				).format(from_currency, to_currency)
			)
		frappe.throw(
			_(
				"Setup the Exchange Rate Provider other than 'Frankfurter' in settings, as default provider does not support currency conversion for {0} to {1}."
			).format(from_currency, to_currency)
		)

	frappe.throw(
		_(
			"Failed to fetch exchange rate from {0} to {1} on {2}. Please check your internet connection or try again later."
		).format(from_currency, to_currency, date)
	)
