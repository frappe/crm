# Copyright (c) 2024, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.model.document import Document
from frappe.frappeclient import FrappeClient
from frappe.utils import get_url_to_form, get_url_to_list
import json

class ERPNextCRMSettings(Document):
	def validate(self):
		if self.enabled:
			self.validate_if_erpnext_installed()
			self.add_quotation_to_option()
			self.create_custom_fields()	
			self.create_crm_form_script()
	
	def validate_if_erpnext_installed(self):
		if not self.is_erpnext_in_different_site:
			if "erpnext" not in frappe.get_installed_apps():
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
			from erpnext.crm.frappe_crm_api import create_custom_fields_for_frappe_crm
			create_custom_fields_for_frappe_crm()
		else:
			self.create_custom_fields_in_remote_site()

	def create_custom_fields_in_remote_site(self):
		client = get_erpnext_site_client(self)
		try:
			client.post_api("erpnext.crm.frappe_crm_api.create_custom_fields_for_frappe_crm")
		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				f"Error while creating custom field in the remote erpnext site: {self.erpnext_site_url}"
			)
			frappe.throw("Error while creating custom field in ERPNext, check error log for more details")

	def create_crm_form_script(self):
		if not frappe.db.exists("CRM Form Script", "Create Quotation from CRM Deal"):
			script = get_crm_form_script()
			frappe.get_doc({
				"doctype": "CRM Form Script",
				"name": "Create Quotation from CRM Deal",
				"dt": "CRM Deal",
				"view": "Form",
				"script": script,
				"enabled": 1,
				"is_standard": 1
			}).insert()

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

def get_erpnext_site_client(erpnext_crm_settings):
	site_url = erpnext_crm_settings.erpnext_site_url
	api_key = erpnext_crm_settings.api_key
	api_secret = erpnext_crm_settings.get_password("api_secret", raise_exception=False)

	return FrappeClient(
		site_url, api_key=api_key, api_secret=api_secret
	)

@frappe.whitelist()
def get_customer_link(crm_deal):
	erpnext_crm_settings = frappe.get_single("ERPNext CRM Settings")
	if not erpnext_crm_settings.enabled:
		frappe.throw(_("ERPNext is not integrated with the CRM"))

	if not erpnext_crm_settings.is_erpnext_in_different_site:
		customer = frappe.db.exists("Customer", {"crm_deal": crm_deal})
		return get_url_to_form("Customer", customer) if customer else ""
	else:
		client = get_erpnext_site_client(erpnext_crm_settings)
		try:
			customer = client.get_list("Customer", {"crm_deal": crm_deal})
			customer = customer[0].get("name") if len(customer) else None
			if customer:
				return f"{erpnext_crm_settings.erpnext_site_url}/app/customer/{customer}"
			else:
				return ""
		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				f"Error while fetching customer in remote site: {erpnext_crm_settings.erpnext_site_url}"
			)
			frappe.throw(_("Error while fetching customer in ERPNext, check error log for more details"))


@frappe.whitelist()
def get_quotation_url(crm_deal, organization):
	erpnext_crm_settings = frappe.get_single("ERPNext CRM Settings")
	if not erpnext_crm_settings.enabled:
		frappe.throw(_("ERPNext is not integrated with the CRM"))

	if not erpnext_crm_settings.is_erpnext_in_different_site:
		quotation_url = get_url_to_list("Quotation")
		return f"{quotation_url}/new?quotation_to=CRM Deal&crm_deal={crm_deal}&party_name={crm_deal}&company={erpnext_crm_settings.erpnext_company}"
	else:
		site_url = erpnext_crm_settings.get("erpnext_site_url")
		quotation_url = f"{site_url}/app/quotation"

		prospect = create_prospect_in_remote_site(crm_deal, erpnext_crm_settings)
		return f"{quotation_url}/new?quotation_to=Prospect&crm_deal={crm_deal}&party_name={prospect}&company={erpnext_crm_settings.erpnext_company}"

def create_prospect_in_remote_site(crm_deal, erpnext_crm_settings):
	try:
		client = get_erpnext_site_client(erpnext_crm_settings)
		doc = frappe.get_doc("CRM Deal", crm_deal)
		contacts = get_contacts(doc)
		address = get_organization_address(doc.organization)
		return client.post_api("erpnext.crm.frappe_crm_api.create_prospect_against_crm_deal",
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
				"contacts": json.dumps(contacts),
				"erpnext_company": erpnext_crm_settings.erpnext_company,
				"address": address.as_dict() if address else None
			},
		)
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			f"Error while creating prospect in remote site: {erpnext_crm_settings.erpnext_site_url}"
		)
		frappe.throw(_("Error while creating prospect in ERPNext, check error log for more details"))

def get_contacts(doc):
	contacts = []
	for c in doc.contacts:
		contacts.append({
			"contact": c.contact,
			"full_name": c.full_name,
			"email": c.email,
			"mobile_no": c.mobile_no,
			"gender": c.gender,
			"is_primary": c.is_primary,
		})
	return contacts

def get_organization_address(organization):
	address = frappe.db.get_value("CRM Organization", organization, "address")
	address = frappe.get_doc("Address", address) if address else None
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
	
	contacts = get_contacts(doc)
	address = get_organization_address(doc.organization)
	customer = {
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
	if not erpnext_crm_settings.is_erpnext_in_different_site:
		from erpnext.crm.frappe_crm_api import create_customer
		create_customer(customer)
	else:
		create_customer_in_remote_site(customer, erpnext_crm_settings)

	frappe.publish_realtime("crm_customer_created")

def create_customer_in_remote_site(customer, erpnext_crm_settings):
	client = get_erpnext_site_client(erpnext_crm_settings)
	try:
		client.post_api("erpnext.crm.frappe_crm_api.create_customer", customer)
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			"Error while creating customer in remote site"
		)
		frappe.throw(_("Error while creating customer in ERPNext, check error log for more details"))

@frappe.whitelist()
def get_crm_form_script():
	return  """
async function setupForm({ doc, call, $dialog, updateField, createToast }) {
	let actions = [];
	let is_erpnext_integration_enabled = await call("frappe.client.get_single_value", {doctype: "ERPNext CRM Settings", field: "enabled"});
	if (!["Lost", "Won"].includes(doc?.status) && is_erpnext_integration_enabled) {
		actions.push({
			label: __("Create Quotation"),
			onClick: async () => {
				let quotation_url = await call(
					"crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.get_quotation_url", 
					{
						crm_deal: doc.name,
						organization: doc.organization
					}
				);

				if (quotation_url) {
					window.open(quotation_url, '_blank');
				}
			}
		})
	}
	if (is_erpnext_integration_enabled) {
		let customer_url = await call("crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.get_customer_link", {
			crm_deal: doc.name
		});
		if (customer_url) {
			actions.push({
				label: __("View Customer"),
				onClick: () => window.open(customer_url, '_blank')
			});
		}
	}
	return {
		actions: actions,
	};
}
"""
