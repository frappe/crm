# Copyright (c) 2024, Frappe and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields as _create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.frappeclient import FrappeClient
from frappe.model.document import Document
from frappe.utils import get_url_to_form, get_url_to_list


def _is_erpnext_installed():
	return "erpnext" in frappe.get_installed_apps()


def _log_and_throw(message: str, title: str | None = None):
	frappe.log_error(frappe.get_traceback(), title or message)
	frappe.throw(_(message))


def _get_enabled_settings():
	settings = frappe.get_single("ERPNext CRM Settings")
	if not settings.enabled:
		frappe.throw(_("ERPNext is not integrated with the CRM"))
	return settings


class ERPNextCRMSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		api_key: DF.Data | None
		api_secret: DF.Password | None
		create_customer_on_status_change: DF.Check
		deal_status: DF.Link | None
		enabled: DF.Check
		erpnext_company: DF.Data | None
		erpnext_site_url: DF.Data | None
		is_erpnext_in_different_site: DF.Check
	# end: auto-generated types

	def validate(self):
		if self.enabled:
			self.validate_if_erpnext_installed()
			self.add_quotation_to_option()
			self.create_custom_fields()
			self.create_crm_form_script()

	def validate_if_erpnext_installed(self):
		if not self.is_erpnext_in_different_site:
			if not _is_erpnext_installed():
				frappe.throw(_("ERPNext is not installed in the current site"))

	def add_quotation_to_option(self):
		if not self.is_erpnext_in_different_site:
			if not frappe.db.exists("Property Setter", {"name": "Quotation-quotation_to-link_filters"}):
				make_property_setter(
					doctype="Quotation",
					fieldname="quotation_to",
					property="link_filters",
					value='[["DocType","name","in", ["Customer", "Lead", "Prospect", "CRM Deal"]]]',
					property_type="JSON",
					validate_fields_for_doctype=False,
				)

	def create_custom_fields(self):
		if not self.is_erpnext_in_different_site:
			try:
				from erpnext.crm.frappe_crm_api import create_custom_fields_for_frappe_crm

				create_custom_fields_for_frappe_crm()
			except ImportError:
				frappe.throw(_("ERPNext is not installed in the current site"))
		else:
			self.create_custom_fields_in_remote_site()

		self.create_custom_fields_in_frappe_crm()

	def create_custom_fields_in_frappe_crm(self):
		custom_fields = {
			"CRM Deal": [
				{
					"fieldname": "erpnext_customer",
					"fieldtype": "Data",
					"label": "Customer in ERPNext",
					"insert_after": "lead_name",
				}
			]
		}
		_create_custom_fields(custom_fields, ignore_validate=True)

	def create_custom_fields_in_remote_site(self):
		client = get_erpnext_site_client(self)
		try:
			client.post_api("erpnext.crm.frappe_crm_api.create_custom_fields_for_frappe_crm")
		except Exception:
			_log_and_throw(
				"Error while creating custom field in ERPNext, check error log for more details",
				f"Error while creating custom field in the remote erpnext site: {self.erpnext_site_url}",
			)

	def create_crm_form_script(self):
		if not frappe.db.exists("CRM Form Script", "Create Quotation from CRM Deal"):
			script = get_crm_form_script()
			frappe.get_doc(
				{
					"doctype": "CRM Form Script",
					"name": "Create Quotation from CRM Deal",
					"dt": "CRM Deal",
					"view": "Form",
					"script": script,
					"enabled": 1,
					"is_standard": 1,
				}
			).insert()

	@frappe.whitelist()
	def reset_erpnext_form_script(self):
		try:
			if frappe.db.exists("CRM Form Script", "Create Quotation from CRM Deal"):
				script = get_crm_form_script()
				frappe.db.set_value("CRM Form Script", "Create Quotation from CRM Deal", "script", script)
				return True
			return False
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Error while resetting form script")
			return False

	@frappe.whitelist()
	def get_external_companies(self):
		if not self.erpnext_site_url or not self.api_key or not self.api_secret:
			return []
		client = get_erpnext_site_client(self)
		return client.get_list("Company", fields=["company_name"])

	@frappe.whitelist()
	def is_erpnext_installed(self):
		return _is_erpnext_installed()


def get_erpnext_site_client(erpnext_crm_settings):
	site_url = erpnext_crm_settings.erpnext_site_url
	api_key = erpnext_crm_settings.api_key
	api_secret = erpnext_crm_settings.get_password("api_secret", raise_exception=False)

	return FrappeClient(site_url, api_key=api_key, api_secret=api_secret)


@frappe.whitelist()
def get_customer_link(crm_deal: str):
	erpnext_crm_settings = _get_enabled_settings()

	if not erpnext_crm_settings.is_erpnext_in_different_site:
		customer = frappe.db.exists("Customer", {"crm_deal": crm_deal})
		if not customer:
			customer = frappe.db.get_value("CRM Deal", crm_deal, "erpnext_customer")
		return get_url_to_form("Customer", customer) if customer else ""

	client = get_erpnext_site_client(erpnext_crm_settings)
	try:
		customer = client.get_list("Customer", filters={"crm_deal": crm_deal})
		customer = customer[0].get("name") if customer else None

		if not customer:
			customer = frappe.db.get_value("CRM Deal", crm_deal, "erpnext_customer")

		if customer:
			return f"{erpnext_crm_settings.erpnext_site_url}/app/customer/{customer}"
		return ""
	except Exception:
		_log_and_throw(
			"Error while fetching customer in ERPNext, check error log for more details",
			f"Error while fetching customer in remote site: {erpnext_crm_settings.erpnext_site_url}",
		)


@frappe.whitelist()
def get_quotation_url(crm_deal: str, organization: str | None = None):
	erpnext_crm_settings = _get_enabled_settings()

	contact = get_primary_contact(crm_deal)
	address = get_organization_address(organization)
	address_name = address.get("name") if address else None

	if not erpnext_crm_settings.is_erpnext_in_different_site:
		base_url = f"{get_url_to_list('Quotation')}/new"
		params = {
			"quotation_to": "CRM Deal",
			"crm_deal": crm_deal,
			"party_name": crm_deal,
			"company": erpnext_crm_settings.erpnext_company,
			"contact_person": contact,
			"customer_address": address_name,
		}
	else:
		site_url = erpnext_crm_settings.get("erpnext_site_url")
		base_url = f"{site_url}/app/quotation/new"
		prospect = create_prospect_in_remote_site(crm_deal, erpnext_crm_settings)
		params = {
			"quotation_to": "Prospect",
			"crm_deal": crm_deal,
			"party_name": prospect,
			"company": erpnext_crm_settings.erpnext_company,
			"contact_person": contact,
			"customer_address": address_name,
		}

	# Filter out None values and build query string
	query_string = "&".join(f"{key}={value}" for key, value in params.items() if value is not None)

	return f"{base_url}?{query_string}"


def create_prospect_in_remote_site(crm_deal, erpnext_crm_settings):
	try:
		client = get_erpnext_site_client(erpnext_crm_settings)
		doc = frappe.get_cached_doc("CRM Deal", crm_deal)
		contacts = get_contacts(doc)
		address = get_organization_address(doc.organization) or None

		if address and not isinstance(address, dict):
			address = address.as_dict()

		return client.post_api(
			"erpnext.crm.frappe_crm_api.create_prospect_against_crm_deal",
			{
				"organization": doc.organization,
				"lead_name": doc.lead_name,
				"no_of_employees": doc.no_of_employees,
				"deal_owner": doc.deal_owner,
				"crm_deal": doc.name,
				"territory": doc.territory,
				"industry": doc.industry,
				"website": doc.website,
				"annual_revenue": doc.annual_revenue,
				"contacts": json.dumps(contacts) if contacts else None,
				"erpnext_company": erpnext_crm_settings.erpnext_company,
				"address": json.dumps(address) if address else None,
			},
		)
	except Exception:
		_log_and_throw(
			"Error while creating prospect in ERPNext, check error log for more details",
			f"Error while creating prospect in remote site: {erpnext_crm_settings.erpnext_site_url}",
		)


def get_primary_contact(crm_deal):
	doc = frappe.get_cached_doc("CRM Deal", crm_deal)
	for c in doc.contacts:
		if c.is_primary:
			return c.contact
	return None


def get_contacts(doc):
	return [
		{
			"contact": c.contact,
			"full_name": c.full_name,
			"email": c.email,
			"mobile_no": c.mobile_no,
			"gender": c.gender,
			"is_primary": c.is_primary,
		}
		for c in doc.contacts
	]


def get_organization_address(organization: str | None = None):
	if not organization:
		return None
	address = frappe.db.get_value("CRM Organization", organization, "address")
	address = frappe.get_cached_doc("Address", address) if address else None
	if not address:
		return None
	return {
		"name": address.name,
		"address_title": address.address_title,
		"address_type": address.address_type,
		"address_line1": address.address_line1,
		"address_line2": address.address_line2,
		"city": address.city,
		"county": address.county,
		"state": address.state,
		"country": address.country,
		"pincode": address.pincode,
	}


def create_customer_in_erpnext(doc, method):
	erpnext_crm_settings = frappe.get_single("ERPNext CRM Settings")
	if (
		not erpnext_crm_settings.enabled
		or not erpnext_crm_settings.create_customer_on_status_change
		or doc.status != erpnext_crm_settings.deal_status
	):
		return

	if not doc.organization:
		frappe.throw(_("Organization is required to create a customer"))

	contacts = get_contacts(doc)
	address = get_organization_address(doc.organization)
	customer_data = {
		"customer_name": doc.organization,
		"customer_group": "All Customer Groups",
		"customer_type": "Company",
		"territory": doc.territory,
		"default_currency": doc.currency,
		"industry": doc.industry,
		"website": doc.website,
		"crm_deal": doc.name,
		"contacts": json.dumps(contacts),
		"address": json.dumps(address) if address else None,
	}

	try:
		if not erpnext_crm_settings.is_erpnext_in_different_site:
			try:
				from erpnext.crm.frappe_crm_api import create_customer
			except ImportError:
				frappe.throw(_("ERPNext is not installed in the current site"))

			customer_name = create_customer(customer_data)
		else:
			client = get_erpnext_site_client(erpnext_crm_settings)
			customer_name = client.post_api("erpnext.crm.frappe_crm_api.create_customer", customer_data)

		if not customer_name:
			_log_and_throw(
				"Error while creating customer in ERPNext, check error log for more details",
				f"Error while creating customer in ERPNext for CRM Deal: {doc.name}",
			)
	except frappe.ValidationError:
		raise
	except Exception:
		_log_and_throw("Error while creating customer in ERPNext, check error log for more details")

	if customer_name:
		frappe.db.set_value("CRM Deal", doc.name, "erpnext_customer", customer_name)
		frappe.publish_realtime("crm_customer_created")


@frappe.whitelist()
def get_crm_form_script():
	return """class CRMDeal {
	onLoad() {
		if (this.doc.__newDocument) return
		call(
			"frappe.client.get_single_value",
			{
				doctype: "ERPNext CRM Settings",
				field: "enabled"
			}
		).then((enabled) => {
			if (enabled) this.doc.trigger('setActions')
		})
	}
	setActions() {
		// Add Create Quotation Button
		this.actions.push({
			label: __("Create Quotation"),
			onClick: () => {
				call(
					"crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.get_quotation_url",
					{
						crm_deal: this.doc.name,
						organization: this.doc.organization
					}
				).then((quotation_url) => {
					if (quotation_url) {
						window.open(quotation_url, '_blank');
					} else {
						toast.error("Error while creating quotation in ERPNext");
					}
				}).catch((e) => {
					toast.error(e.messages[0] || "Error while creating quotation in ERPNext. Check error log in ERPNext for more details");
				});
			}
		})

		// Add View Customer Button
		call("crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.get_customer_link", {
			crm_deal: this.doc.name
		}).then((customer_url) => {
			if (customer_url) {
				this.actions.push({
					label: __("View Customer"),
					onClick: () => window.open(customer_url, '_blank')
				});
			}
		}).catch((e) => {
			toast.error(e.messages[0] || "Error while fetching customer link from ERPNext. Check error log in ERPNext for more details");
		});
	}
}
"""
