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
		self.add_quotation_to_option()
		self.create_custom_fields()	
		self.create_crm_form_script()

	def add_quotation_to_option(self):
		if not frappe.db.exists("Property Setter", {"name": "Quotation-quotation_to-link_filters"}):
			make_property_setter(
				doctype="Quotation",
				fieldname="quotation_to",
				property="link_filters",
				value='[["DocType","name","in", ["Customer", "Lead", "Prospect", "Opportunity"]]]',
				property_type="JSON",
				validate_fields_for_doctype=False,
			)

	def create_custom_fields(self):
		from erpnext.crm.frappe_crm_api import create_custom_fields_for_frappe_crm
		create_custom_fields_for_frappe_crm()

	def create_crm_form_script(self):
		if not frappe.db.exists("CRM Form Script", "Create Quotation from Opportunity"):
			script = get_crm_form_script()
			frappe.get_doc({
				"doctype": "CRM Form Script",
				"name": "Create Quotation from Opportunity",
				"dt": "Opportunity",
				"view": "Form",
				"script": script,
				"enabled": 1,
				"is_standard": 1
			}).insert()

	@frappe.whitelist()
	def reset_erpnext_form_script(self):
		try:
			if frappe.db.exists("CRM Form Script", "Create Quotation from Opportunity"):
				script = get_crm_form_script()
				frappe.db.set_value("CRM Form Script", "Create Quotation from Opportunity", "script", script)
				return True
			return False
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Error while resetting form script")
			return False

@frappe.whitelist()
def get_customer_link(opportunity):
	erpnext_crm_settings = frappe.get_single("ERPNext CRM Settings")
	if not erpnext_crm_settings.enabled:
		frappe.throw(_("ERPNext is not integrated with the CRM"))

	customer = frappe.db.exists("Customer", {"opportunity": opportunity})
	return get_url_to_form("Customer", customer) if customer else ""

@frappe.whitelist()
def get_quotation_url(opportunity, customer):
	erpnext_crm_settings = frappe.get_single("ERPNext CRM Settings")
	if not erpnext_crm_settings.enabled:
		frappe.throw(_("ERPNext is not integrated with the CRM"))

	quotation_url = get_url_to_list("Quotation")
	return f"{quotation_url}/new?quotation_to=Opportunity&opportunity={opportunity}&party_name={opportunity}&company={erpnext_crm_settings.erpnext_company}"


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

def get_customer_address(customer):
	address = frappe.db.get_value("Customer", customer, "customer_primary_address")
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
		not erpnext_crm_settings.create_customer_on_status_change
		or doc.status != erpnext_crm_settings.deal_status
	):
		return
	
	contacts = get_contacts(doc)
	address = get_customer_address(doc.customer)
	customer = {
		"customer_name": doc.customer,
		"customer_group": "All Customer Groups",
		"customer_type": "Company",
		"territory": doc.territory,
		"default_currency": doc.currency,
		"industry": doc.industry,
		"website": doc.website,
		"opportunity": doc.name,
		"contacts": json.dumps(contacts),
		"address": json.dumps(address) if address else None,
	}
	from erpnext.crm.frappe_crm_api import create_customer
	create_customer(customer)

	frappe.publish_realtime("crm_customer_created")

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
					"next_crm.ncrm.doctype.erpnext_crm_settings.erpnext_crm_settings.get_quotation_url", 
					{
						opportunity: doc.name,
						customer: doc.customer
					}
				);

				if (quotation_url) {
					window.open(quotation_url, '_blank');
				}
			}
		})
	}
	if (is_erpnext_integration_enabled) {
		let customer_url = await call("next_crm.ncrm.doctype.erpnext_crm_settings.erpnext_crm_settings.get_customer_link", {
			opportunity: doc.name
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
