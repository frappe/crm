import frappe
from frappe.integrations.utils import make_get_request

FB_GRAPH_API_BASE = "https://graph.facebook.com"
FB_GRAPH_API_VERSION = "v23.0"


def get_fb_graph_api_url(endpoint: str) -> str:
	if endpoint.startswith("/"):
		endpoint = endpoint[1:]

	return f"{FB_GRAPH_API_BASE}/{FB_GRAPH_API_VERSION}/{endpoint}"


class FacebookSyncSource:
	def __init__(
		self,
		access_token: str,
		form_id: str,
		source_name: str | None = None,
	):
		self.access_token = access_token
		self.form_id = form_id
		self.source_name = source_name

	def get_api_url(self, endpoint: str) -> str:
		return get_fb_graph_api_url(endpoint)

	def sync(self):
		leads = self.fetch_leads()
		question_to_field_map = self.get_form_questions_mapping()

		for lead in leads:
			lead_data = {item["name"]: item["values"][0] for item in lead["field_data"]}
			crm_lead_data = {
				question_to_field_map.get(k): v for k, v in lead_data.items() if k in question_to_field_map
			}
			crm_lead_data["source"] = "Facebook"
			crm_lead_data["facebook_lead_id"] = lead["id"]

			try:
				frappe.get_doc(
					{
						"doctype": "CRM Lead",
						**crm_lead_data,
					}
				).insert(ignore_permissions=True)
			except frappe.UniqueValidationError:
				# Skip duplicate leads based on facebook_lead_id
				# TODO: de-duplication based on field values
				self.create_failure_log(lead, "Duplicate")
			except Exception:
				self.create_failure_log(lead)

		self.update_last_synced_at()

	def fetch_leads(self):
		url = self.get_api_url(f"/{self.form_id}/leads")

		if self.last_synced_at:
			timestamp = frappe.utils.data.get_timestamp(self.last_synced_at)
			filtering = (
				f"filtering=[{{'field':'time_created','operator':'GREATER_THAN','value':{timestamp}}}]"
			)
			url = f"{url}?{filtering}"

		return make_get_request(
			url,
			params={
				"access_token": self.access_token,
				"fields": "id,created_time,field_data",
				"limit": 100000,  # TODO: pagination
			},
		).get("data", [])

	def get_form_questions_mapping(self):
		form_questions = frappe.db.get_all(
			"Facebook Lead Form Question",
			filters={"parent": self.form_id},
			fields=["key", "mapped_to_crm_field"],
		)

		return {q["key"]: q["mapped_to_crm_field"] for q in form_questions if q["mapped_to_crm_field"]}

	@property
	def last_synced_at(self):
		return frappe.db.get_value(
			"Lead Sync Source", self.source_name or {"facebook_lead_form": self.form_id}, "last_synced_at"
		)

	def create_failure_log(self, lead_data: dict | None = None, type: str = "Failure"):
		return frappe.get_doc(
			{
				"doctype": "Failed Lead Sync Log",
				"type": type,
				"lead_data": frappe.as_json(lead_data),
				"source": self.get_source_name()
			}
		).insert(ignore_permissions=True)

	def update_last_synced_at(self):
		frappe.db.set_value(
			"Lead Sync Source",
			self.source_name or {"facebook_lead_form": self.form_id},
			"last_synced_at",
			frappe.utils.now(),
		)

	def get_source_name(self):
		if self.source_name:
			return self.source_name

		return frappe.db.get_value("Lead Sync Source", {"facebook_lead_form": self.form_id}, "name")


@frappe.whitelist()
def fetch_and_store_pages_from_facebook(access_token: str) -> list[dict]:
	if not access_token:
		frappe.throw(frappe._("Access token is required"))

	account_details = get_fb_account_details(access_token)
	if not account_details.get("id"):
		frappe.throw(frappe._("Invalid access token provided for Facebook."))

	url = get_fb_graph_api_url("/me/accounts")
	pages = make_get_request(url, params={"access_token": access_token}).get("data", [])
	for page in pages:
		page_id = page["id"]
		already_synced = frappe.db.exists("Facebook Page", page_id)
		if not already_synced:
			create_facebook_page_in_db(page, account_details)
		forms = fetch_and_store_leadgen_forms_from_facebook(page_id, page["access_token"])
		page["forms"] = forms

	return pages


def get_fb_account_details(access_token: str) -> dict:
	url = get_fb_graph_api_url("me")
	try:
		response = make_get_request(url, params={"access_token": access_token})
	except Exception as _:
		frappe.throw(frappe._("Please check your access token"))
	return response


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


def fetch_and_store_leadgen_forms_from_facebook(page_id: str, page_access_token: str) -> list[dict]:
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

	return forms


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
	form_doc.insert(ignore_permissions=True)


@frappe.whitelist()
def get_pages_with_forms() -> list[dict]:
	pages = frappe.db.get_all("Facebook Page", fields=["id", "name"])
	for page in pages:
		forms = frappe.db.get_all("Facebook Lead Form", filters={"page": page["id"]}, fields=["id", "name"])
		page["forms"] = forms
	return pages


def validate_duplicate(lead: dict, field_mapping: dict):
	# if a lead exists with
	pass
