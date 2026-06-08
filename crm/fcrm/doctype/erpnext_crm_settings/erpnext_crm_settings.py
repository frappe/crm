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

		from crm.fcrm.doctype.crm_product_sync_issue.crm_product_sync_issue import CRMProductSyncIssue

		api_key: DF.Data | None
		api_secret: DF.Password | None
		create_customer_on_status_change: DF.Check
		deal_status: DF.Link | None
		enabled: DF.Check
		erpnext_company: DF.Data | None
		erpnext_site_url: DF.Data | None
		is_erpnext_in_different_site: DF.Check
		sync_issues: DF.Table[CRMProductSyncIssue]
	# end: auto-generated types

	def validate(self):
		old = self.get_doc_before_save()
		was_active = bool(old and old.enabled and not old.is_erpnext_in_different_site)
		if self.enabled:
			self.validate_if_erpnext_installed()
			self.add_quotation_to_option()
			self.create_custom_fields()
			self.create_crm_form_script()
			self.grant_item_access_to_sales_roles()
			if not was_active and not self.is_erpnext_in_different_site:
				from crm.fcrm.doctype.crm_product.reconcile_job import enqueue_reconciliation

				enqueue_reconciliation()

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
			],
			"CRM Product": [
				{
					"fieldname": "erpnext_item_code",
					"fieldtype": "Data",
					"label": "Item Code in ERPNext",
					"read_only": 1,
					"insert_after": "product_code",
				}
			],
		}
		if frappe.db.exists("DocType", "Item"):
			custom_fields["Item"] = [
				{
					"fieldname": "crm_product_code",
					"fieldtype": "Data",
					"label": "CRM Product",
					"read_only": 1,
					"no_copy": 1,
					"insert_after": "item_code",
				}
			]
		if frappe.db.exists("DocType", "Quotation"):
			custom_fields["Quotation"] = [
				{
					"fieldname": "crm_deal",
					"fieldtype": "Data",
					"label": "Frappe CRM Deal",
					"read_only": 1,
					"insert_after": "party_name",
				}
			]
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

	def grant_item_access_to_sales_roles(self):
		if self.is_erpnext_in_different_site:
			return
		if not frappe.db.exists("DocType", "Item"):
			return
		from frappe.permissions import add_permission, update_permission_property

		for role in ("Sales User", "Sales Manager"):
			if frappe.db.exists("Custom DocPerm", {"parent": "Item", "role": role, "permlevel": 0}):
				continue
			add_permission("Item", role, 0, "write")
			for prop in ("create", "delete", "share", "print", "report", "export"):
				update_permission_property("Item", role, 0, prop, 1)

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

	@frappe.whitelist()
	def run_product_sync(self):
		if not self.enabled or self.is_erpnext_in_different_site:
			frappe.throw(_("ERPNext integration must be enabled on the same site"))
		from crm.fcrm.doctype.crm_product.reconcile_job import enqueue_reconciliation

		enqueue_reconciliation()
		return True


@frappe.whitelist()
def get_open_sync_issues():
	if not frappe.has_permission("CRM Product", "read"):
		return []
	settings = frappe.get_single("ERPNext CRM Settings")
	return [
		{
			"name": issue.name,
			"product": issue.product,
			"kind": issue.kind,
			"detail": issue.detail,
			"detected_on": issue.detected_on,
		}
		for issue in settings.sync_issues
		if not issue.dismissed
	]


@frappe.whitelist()
def dismiss_sync_issue(issue_name: str):
	settings = frappe.get_single("ERPNext CRM Settings")
	for issue in settings.sync_issues:
		if issue.name == issue_name:
			issue.dismissed = 1
			settings.save()
			return True
	return False


def get_erpnext_site_client(erpnext_crm_settings):
	site_url = erpnext_crm_settings.erpnext_site_url
	api_key = erpnext_crm_settings.api_key
	api_secret = erpnext_crm_settings.get_password("api_secret", raise_exception=False)

	return FrappeClient(site_url, api_key=api_key, api_secret=api_secret)


def get_local_customer(crm_deal: str):
	customer = frappe.db.exists("Customer", {"crm_deal": crm_deal})
	if not customer:
		customer = frappe.db.get_value("CRM Deal", crm_deal, "erpnext_customer")
	return customer


@frappe.whitelist()
def get_customer_link(crm_deal: str):
	erpnext_crm_settings = _get_enabled_settings()

	if not erpnext_crm_settings.is_erpnext_in_different_site:
		customer = get_local_customer(crm_deal)
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
		customer = get_local_customer(crm_deal)
		base_url = f"{get_url_to_list('Quotation')}/new"
		params = {
			"quotation_to": "Customer" if customer else "CRM Deal",
			"crm_deal": crm_deal,
			"party_name": customer or crm_deal,
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


@frappe.whitelist()
def prefill_quotation_items(crm_deal: str):
	if not frappe.db.exists("CRM Deal", crm_deal):
		return []
	deal = frappe.get_doc("CRM Deal", crm_deal)
	items = []
	for row in deal.products:
		item_code = frappe.db.get_value("CRM Product", row.product_code, "erpnext_item_code")
		if not item_code:
			continue
		items.append(
			{
				"item_code": item_code,
				"qty": row.qty or 1,
				"price_list_rate": row.rate or 0,
				"discount_percentage": row.discount_percentage or 0,
			}
		)
	return items


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

	create_customer_from_deal(doc, erpnext_crm_settings)


def create_customer_on_sales_order(doc, method):
	if doc.customer:
		return

	crm_deal = get_deal_from_sales_order(doc)
	customer = check_customer_for_deal(crm_deal) if crm_deal else None
	if customer:
		doc.customer = customer


def check_customer_for_deal(crm_deal: str):
	"""Return the ERPNext Customer for the deal and create it if it doesn't exist"""
	erpnext_crm_settings = frappe.get_single("ERPNext CRM Settings")
	if not erpnext_crm_settings.enabled or erpnext_crm_settings.is_erpnext_in_different_site:
		return None
	if not crm_deal or not frappe.db.exists("CRM Deal", crm_deal):
		return None

	customer = get_local_customer(crm_deal)
	if not customer:
		customer = create_customer_from_deal(
			frappe.get_cached_doc("CRM Deal", crm_deal), erpnext_crm_settings
		)
	return customer


@frappe.whitelist()
def check_customer_for_quotation(quotation: str):
	"""Create/fetch the Customer for the CRM Deal behind a quotation. Called when a
	Sales Order form is opened from a CRM Deal quotation that has no customer yet.
	"""
	crm_deal = frappe.db.get_value("Quotation", quotation, "crm_deal")
	if not crm_deal:
		return None
	return check_customer_for_deal(crm_deal)


def get_deal_from_sales_order(doc):
	for item in doc.items:
		quotation = item.get("prevdoc_docname")
		if quotation:
			crm_deal = frappe.db.get_value("Quotation", quotation, "crm_deal")
			if crm_deal:
				return crm_deal
	return None


def create_customer_from_deal(doc, erpnext_crm_settings):
	contacts = get_contacts(doc)
	address = get_organization_address(doc.organization)

	if doc.organization:
		customer_title = doc.organization
		customer_type = "Company"
	else:
		primary_contact = next((c for c in contacts if c.get("is_primary")), None)
		customer_title = (primary_contact or {}).get("full_name") or doc.lead_name
		if not customer_title:
			frappe.throw(_("Organization or a primary Contact is required to create a customer"))
		customer_type = "Individual"

	customer_data = {
		"customer_name": customer_title,
		"customer_type": customer_type,
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

			if doc.territory and not frappe.db.exists("Territory", doc.territory):
				customer_data["territory"] = ""

			if doc.industry and not frappe.db.exists("Industry Type", doc.industry):
				customer_data["industry"] = ""

			customer_name = create_customer(customer_data)
		else:
			client = get_erpnext_site_client(erpnext_crm_settings)

			if doc.territory and not client.get_list("Territory", filters={"name": doc.territory}):
				customer_data["territory"] = ""

			if doc.industry and not client.get_list("Industry Type", filters={"name": doc.industry}):
				customer_data["industry"] = ""

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

	return customer_name


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
