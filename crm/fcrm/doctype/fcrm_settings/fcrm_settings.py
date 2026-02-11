# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe import _
from frappe.custom.doctype.property_setter.property_setter import delete_property_setter, make_property_setter
from frappe.model.document import Document

from crm.install import after_install


class FCRMSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.desk.doctype.event_notifications.event_notifications import EventNotifications
		from frappe.types import DF

		from crm.fcrm.doctype.crm_dropdown_item.crm_dropdown_item import CRMDropdownItem

		access_key: DF.Data | None
		all_day_event_notifications: DF.Table[EventNotifications]
		auto_update_expected_deal_value: DF.Check
		brand_logo: DF.Attach | None
		brand_name: DF.Data | None
		currency: DF.Link | None
		default_calendar_view: DF.Literal["Daily", "Weekly", "Monthly"]
		dropdown_items: DF.Table[CRMDropdownItem]
		enable_forecasting: DF.Check
		event_notifications: DF.Table[EventNotifications]
		favicon: DF.Attach | None
		service_provider: DF.Literal["frankfurter.app", "exchangerate.host"]
	# end: auto-generated types

	@frappe.whitelist()
	def restore_defaults(self, force=False):
		after_install(force)

	def validate(self):
		self.do_not_allow_to_delete_if_standard()
		self.setup_forecasting()
		self.make_currency_read_only()

	def do_not_allow_to_delete_if_standard(self):
		if not self.has_value_changed("dropdown_items"):
			return
		old_items = self.get_doc_before_save().get("dropdown_items")
		standard_new_items = [d.name1 for d in self.dropdown_items if d.is_standard]
		standard_old_items = [d.name1 for d in old_items if d.is_standard]
		deleted_standard_items = set(standard_old_items) - set(standard_new_items)
		if deleted_standard_items:
			standard_dropdown_items = get_standard_dropdown_items()
			if not deleted_standard_items.intersection(standard_dropdown_items):
				return
			frappe.throw(_("Cannot delete standard items {0}").format(", ".join(deleted_standard_items)))

	def setup_forecasting(self):
		if self.has_value_changed("enable_forecasting"):
			if not self.enable_forecasting:
				delete_property_setter(
					"CRM Deal",
					"reqd",
					"expected_closure_date",
				)
				delete_property_setter(
					"CRM Deal",
					"reqd",
					"expected_deal_value",
				)
			else:
				make_property_setter(
					"CRM Deal",
					"expected_closure_date",
					"reqd",
					1 if self.enable_forecasting else 0,
					"Check",
				)
				make_property_setter(
					"CRM Deal",
					"expected_deal_value",
					"reqd",
					1 if self.enable_forecasting else 0,
					"Check",
				)

	def make_currency_read_only(self):
		if self.currency and self.has_value_changed("currency"):
			make_property_setter(
				"FCRM Settings",
				"currency",
				"read_only",
				1,
				"Check",
			)


def get_standard_dropdown_items():
	return [item.get("name1") for item in frappe.get_hooks("standard_dropdown_items")]


def after_migrate():
	sync_table("dropdown_items", "standard_dropdown_items")


def sync_table(key, hook):
	crm_settings = FCRMSettings("FCRM Settings")
	existing_items = {d.name1: d for d in crm_settings.get(key)}
	new_standard_items = {}

	# add new items
	count = 0  # maintain count because list may come from seperate apps
	for item in frappe.get_hooks(hook):
		if item.get("name1") not in existing_items:
			crm_settings.append(key, item, count)
		new_standard_items[item.get("name1")] = True
		count += 1

	# remove unused items
	items = crm_settings.get(key)
	items = [item for item in items if not (item.is_standard and (item.name1 not in new_standard_items))]
	crm_settings.set(key, items)

	crm_settings.save()


def create_forecasting_script():
	if not frappe.db.exists("CRM Form Script", "Forecasting Script"):
		script = get_forecasting_script()
		frappe.get_doc(
			{
				"doctype": "CRM Form Script",
				"name": "Forecasting Script",
				"dt": "CRM Deal",
				"view": "Form",
				"script": script,
				"enabled": 1,
				"is_standard": 1,
			}
		).insert()


def get_forecasting_script():
	return """class CRMDeal {
    async status() {
        await this.doc.trigger('updateProbability')
    }
    async updateProbability() {
        let status = await call("frappe.client.get_value", {
            doctype: "CRM Deal Status",
            fieldname: "probability",
            filters: { name: this.doc.status },
        })

        this.doc.probability = status.probability
    }
}"""


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
	settings = FCRMSettings("FCRM Settings")
	if settings and settings.service_provider == "exchangerate.host":
		api_used = "exchangerate.host"
		if not settings.access_key:
			frappe.throw(
				_("Access Key is required for Service Provider: {0}").format(
					frappe.bold(settings.service_provider)
				)
			)

		params = {
			"access_key": settings.access_key,
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
					"Ask your manager to set up the Exchange Rate Provider, as default provider does not support currency conversion for {0} to {1}."
				).format(from_currency, to_currency)
			)
		else:
			frappe.throw(
				_(
					"Setup the Exchange Rate Provider as 'Exchangerate Host' in settings, as default provider does not support currency conversion for {0} to {1}."
				).format(from_currency, to_currency)
			)

	frappe.throw(
		_(
			"Failed to fetch exchange rate from {0} to {1} on {2}. Please check your internet connection or try again later."
		).format(from_currency, to_currency, date)
	)
