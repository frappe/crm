# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Facebook Login (authorization-code flow) for the Lead Ads integration.

Flow: Settings modal → `get_login_url` → user authorizes on facebook.com →
Meta redirects the browser to `callback` → code→token→long-lived token →
pages + forms are synced. State is HMAC-signed to prevent CSRF.
"""

import base64
import hashlib
import hmac
import json
import time
from urllib.parse import quote, urlencode

import frappe
from frappe import _
from frappe.utils import add_to_date, get_url, now_datetime

from crm.integrations.meta.client import (
	MetaAPIError,
	exchange_code_for_token,
	exchange_for_long_lived_token,
	get_settings,
	graph_get,
	graph_get_paginated,
)

# Minimal production scope set for reading leads + subscribing pages:
# - pages_show_list: list the user's pages (/me/accounts)
# - pages_read_engagement + pages_manage_metadata: read page data, subscribe the
#   app to the page's leadgen webhook (/{page}/subscribed_apps)
# - leads_retrieval: read /{form}/leads and /{leadgen_id}
# - pages_manage_ads + ads_management: leads_retrieval dependencies (App Review pair)
# - business_management: pages owned via Business Manager
SCOPES = (
	"pages_show_list",
	"pages_read_engagement",
	"pages_manage_metadata",
	"pages_manage_ads",
	"leads_retrieval",
	"ads_management",
	"business_management",
)

MANAGER_ROLES = {"System Manager", "Sales Manager"}


def _check_manager():
	if not MANAGER_ROLES & set(frappe.get_roles()):
		frappe.throw(_("Only sales managers can manage the Meta integration"), frappe.PermissionError)


def _redirect_uri() -> str:
	return get_url("/api/method/crm.integrations.meta.oauth.callback")


def _sign_state(payload: str) -> str:
	secret = (frappe.local.conf.get("encryption_key") or frappe.local.site).encode()
	return hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()[:24]


@frappe.whitelist()
def get_login_url() -> dict:
	"""The facebook.com dialog URL the browser should visit to connect."""
	_check_manager()
	settings = get_settings()
	if not settings.app_id or not settings.get_password("app_secret", raise_exception=False):
		frappe.throw(_("Set the Meta App ID and App Secret first"))

	payload = json.dumps({"u": frappe.session.user, "t": int(time.time())})
	state = f"{base64.urlsafe_b64encode(payload.encode()).decode()}.{_sign_state(payload)}"
	params = {
		"client_id": settings.app_id,
		"redirect_uri": _redirect_uri(),
		"state": state,
		"scope": ",".join(SCOPES),
		"response_type": "code",
	}
	return {"login_url": f"https://www.facebook.com/v23.0/dialog/oauth?{urlencode(params)}"}


@frappe.whitelist(methods=["GET"])
def callback(code: str | None = None, state: str | None = None, **kwargs):
	"""OAuth redirect target: runs in the connecting user's browser session."""
	_check_manager()
	if not code or not state:
		_redirect_back(error=kwargs.get("error_description") or _("Authorization was cancelled"))
		return

	try:
		encoded, signature = state.rsplit(".", 1)
		payload = base64.urlsafe_b64decode(encoded.encode()).decode()
		if not hmac.compare_digest(signature, _sign_state(payload)):
			frappe.throw(_("Invalid state"))
		parsed = json.loads(payload)
		if int(time.time()) - int(parsed.get("t") or 0) > 600:
			frappe.throw(_("Login expired, please retry"))
	except Exception:
		_redirect_back(error=_("Invalid or expired login attempt"))
		return

	try:
		short = exchange_code_for_token(code, _redirect_uri())
		long_lived = exchange_for_long_lived_token(short["access_token"])
		user_token = long_lived["access_token"]
		expires_in = int(long_lived.get("expires_in") or 0)

		me = graph_get("me", user_token, {"fields": "id,name"})

		settings = frappe.get_doc("CRM Meta Settings")
		settings.user_access_token = user_token
		settings.connected_user_id = me.get("id")
		settings.connected_user_name = me.get("name")
		settings.user_token_expires_at = (
			add_to_date(now_datetime(), seconds=expires_in) if expires_in else None
		)
		settings.save(ignore_permissions=True)

		sync_pages_and_forms(user_token)
		frappe.db.commit()
		_redirect_back()
	except MetaAPIError as exc:
		frappe.log_error(frappe.get_traceback(), "Meta OAuth callback failed")
		_redirect_back(error=str(exc))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Meta OAuth callback failed")
		_redirect_back(error=_("Connection failed, see error log"))


def _redirect_back(error: str | None = None):
	target = "/crm?settings=" + quote("Meta Lead Ads")
	if error:
		target += f"&meta_error={quote(error[:300])}"
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = target


def sync_pages_and_forms(user_token: str) -> list[dict]:
	"""Upsert the user's pages (with long-lived page tokens) and their forms."""
	pages = list(
		graph_get_paginated("me/accounts", user_token, {"fields": "id,name,category,access_token,tasks"})
	)
	for page in pages:
		upsert_page(page)
		try:
			sync_forms_for_page(page["id"], page["access_token"])
		except MetaAPIError:
			frappe.log_error(frappe.get_traceback(), f"Meta: form sync failed for page {page['id']}")
	return pages


def upsert_page(page: dict) -> None:
	if frappe.db.exists("Facebook Page", page["id"]):
		doc = frappe.get_doc("Facebook Page", page["id"])
		doc.page_name = page.get("name")
		doc.category = page.get("category")
		doc.access_token = page.get("access_token")
		doc.token_valid = 1
		doc.save(ignore_permissions=True)
	else:
		frappe.get_doc(
			{
				"doctype": "Facebook Page",
				"id": page["id"],
				"page_name": page.get("name"),
				"category": page.get("category"),
				"access_token": page.get("access_token"),
				"token_valid": 1,
			}
		).insert(ignore_permissions=True)


def sync_forms_for_page(page_id: str, page_token: str) -> None:
	"""Upsert leadgen forms, refreshing questions while keeping existing mappings."""
	for form in graph_get_paginated(
		f"{page_id}/leadgen_forms", page_token, {"fields": "id,name,status,questions"}
	):
		if frappe.db.exists("Facebook Lead Form", form["id"]):
			doc = frappe.get_doc("Facebook Lead Form", form["id"])
			doc.form_name = form.get("name")
			doc.form_status = form.get("status")
			merge_questions(doc, form.get("questions") or [])
			doc.flags.ignore_validate = True
			doc.save(ignore_permissions=True)
		else:
			doc = frappe.get_doc(
				{
					"doctype": "Facebook Lead Form",
					"id": form["id"],
					"form_name": form.get("name"),
					"form_status": form.get("status"),
					"page": page_id,
					"questions": [
						{**question_row(q), "mapped_to_crm_field": default_mapping(q)}
						for q in form.get("questions") or []
					],
				}
			)
			doc.flags.ignore_validate = True
			doc.insert(ignore_permissions=True)


def question_row(q: dict) -> dict:
	return {"key": q.get("key"), "label": q.get("label"), "type": q.get("type"), "id": q.get("id")}


DEFAULT_QUESTION_MAP = {
	"FULL_NAME": "first_name",
	"FIRST_NAME": "first_name",
	"LAST_NAME": "last_name",
	"EMAIL": "email",
	"PHONE": "mobile_no",
	"COMPANY_NAME": "organization",
	"JOB_TITLE": "job_title",
	"WEBSITE": "website",
}


def default_mapping(q: dict) -> str | None:
	return DEFAULT_QUESTION_MAP.get((q.get("type") or "").upper())


def merge_questions(doc, questions: list[dict]) -> None:
	"""Refresh question metadata without losing manual field mappings."""
	existing = {row.key: row for row in doc.questions}
	doc.questions = []
	for q in questions:
		row = question_row(q)
		previous = existing.get(row["key"])
		row["mapped_to_crm_field"] = (
			previous.mapped_to_crm_field if previous and previous.mapped_to_crm_field else default_mapping(q)
		)
		doc.append("questions", row)
