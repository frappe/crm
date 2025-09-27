# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.integrations.utils import make_get_request
from frappe.model.document import Document

FB_GRAPH_API_BASE = "https://graph.facebook.com"
FB_GRAPH_API_VERSION = "v23.0"


def get_fb_graph_api_url(endpoint: str) -> str:
	if endpoint.startswith("/"):
		endpoint = endpoint[1:]

	return f"{FB_GRAPH_API_BASE}/{FB_GRAPH_API_VERSION}/{endpoint}"


class LeadSyncSource(Document):
	def before_save(self):
		if self.type == "Facebook" and self.access_token:
			fetch_and_store_pages_from_facebook(self.access_token)
		pass

	@frappe.whitelist()
	def sync_leads(self):
		if self.type == "Facebook" and self.access_token:
			sync_leads_from_facebook(self.access_token, self.facebook_lead_form)


def sync_leads_from_facebook(access_token: str, lead_form_id: str) -> None:
	url = get_fb_graph_api_url(f"/{lead_form_id}/leads")
	leads = make_get_request(
		url,
		params={
			"access_token": access_token,
			"fields": "id,created_time,field_data",
			"limit": 15000,
		},
	).get("data", [])
	for lead in leads:
		frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": lead["field_data"][0]["values"][0],
				"source": "Facebook",
			}
		).insert(ignore_permissions=True)


def fetch_and_store_pages_from_facebook(access_token: str) -> None:
	account_details = get_fb_account_details(access_token)
	if not account_details.get("id"):
		frappe.log_error("Invalid access token provided for Facebook.", "Lead Sync Source")
		return

	url = get_fb_graph_api_url("/me/accounts")
	pages = make_get_request(url, params={"access_token": access_token}).get("data", [])
	for page in pages:
		page_id = page["id"]
		already_synced = frappe.db.exists("Facebook Page", page_id)
		if not already_synced:
			create_facebook_page_in_db(page, account_details)
		fetch_and_store_leadgen_forms_from_facebook(page_id, page["access_token"])


def get_fb_account_details(access_token: str) -> dict:
	url = get_fb_graph_api_url("me")
	return make_get_request(url, params={"access_token": access_token})


def create_facebook_page_in_db(page: dict, account_details: dict) -> None:
	frappe.get_doc(
		{
			"doctype": "Facebook Page",
			"page_name": page["name"],
			"id": page["id"],
			"category": page["category"],
			"access_token": page["access_token"],
			"account_id": account_details["id"],
		}
	).insert(ignore_permissions=True)


def fetch_and_store_leadgen_forms_from_facebook(page_id: str, page_access_token: str) -> None:
	fields = "id,name,questions"
	url = get_fb_graph_api_url(f"/{page_id}/leadgen_forms")
	forms = make_get_request(
		url,
		params={
			"access_token": page_access_token,
			"fields": fields,
			"limit": 15000,
		},
	).get("data", [])
	for form in forms:
		form_id = form["id"]
		already_synced = frappe.db.exists("Facebook Lead Form", form_id)
		if already_synced:
			continue
		create_facebook_lead_form_in_db(form, page_id)


def create_facebook_lead_form_in_db(form: dict, page_id: str) -> None:
	form_doc = frappe.get_doc(
		{
			"doctype": "Facebook Lead Form",
			"form_name": form["name"],
			"id": form["id"],
			"page": page_id,
			"questions": form["questions"],
		}
	)

	frappe.errprint(form_doc.as_dict())
	form_doc.insert(ignore_permissions=True)
