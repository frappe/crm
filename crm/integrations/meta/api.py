# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Settings-modal API for the Meta Lead Ads integration (manager only)."""

import json

import frappe
from frappe import _
from frappe.utils import get_url

from crm.integrations.meta.client import (
	MetaAPIError,
	get_app_id,
	get_app_secret,
	get_settings,
	graph_get,
	graph_post,
	is_managed_app,
)
from crm.integrations.meta.leads import backfill_form, get_page_token
from crm.integrations.meta.oauth import _check_manager, hub_url, is_hub, sync_pages_and_forms

WEBHOOK_PATH = "/api/method/crm.integrations.meta.webhook.handle"


@frappe.whitelist()
def get_status() -> dict:
	_check_manager()
	settings = get_settings()
	return {
		"app_id": get_app_id(),
		"has_app_secret": bool(get_app_secret()),
		# managed: the app belongs to the provider and is shared by every client
		# site, so this site shows no developer credentials and no webhook setup
		"managed": is_managed_app(),
		"hub": hub_url(),
		# this site owns the app's callbacks (single-site setup, or the hub)
		"is_hub": is_hub(),
		"webhook_url": get_url(WEBHOOK_PATH),
		"webhook_verify_token": settings.webhook_verify_token or "",
		"connected": bool(settings.get_password("user_access_token", raise_exception=False)),
		"connected_user_name": settings.connected_user_name or "",
		"user_token_expires_at": str(settings.user_token_expires_at or ""),
	}


@frappe.whitelist(methods=["POST"])
def save_app_settings(app_id: str, app_secret: str | None = None) -> dict:
	_check_manager()
	if is_managed_app():
		frappe.throw(_("The Meta app is managed by your provider and cannot be changed here"))
	settings = frappe.get_doc("CRM Meta Settings")
	settings.app_id = (app_id or "").strip()
	if app_secret:  # write-only: empty keeps the stored secret
		settings.app_secret = app_secret
	settings.save()
	frappe.clear_document_cache("CRM Meta Settings", "CRM Meta Settings")
	frappe.db.commit()  # the webhook handshake below hits this site re-entrantly

	# best-effort: register the app-level webhook subscription right away so
	# nothing has to be configured by hand on developers.facebook.com
	status = get_status()
	try:
		status["webhook"] = configure_webhook()
	except Exception as exc:
		status["webhook"] = {"configured": False, "error": str(exc)[:300]}
	return status


def _app_token() -> str:
	if not get_app_id() or not get_app_secret():
		frappe.throw(_("Set the Meta App ID and App Secret first"))
	return f"{get_app_id()}|{get_app_secret()}"


@frappe.whitelist(methods=["POST"])
def configure_webhook() -> dict:
	"""Register the Page→leadgen webhook subscription on the Meta app via API
	(same as the Webhooks product page on developers.facebook.com).

	Meta verifies the callback synchronously (GET handshake against this site),
	so the site must be publicly reachable over HTTPS."""
	_check_manager()
	settings = get_settings()
	if not is_hub():
		# one shared app has a single callback: the hub owns it, and it fans
		# notifications out to the client site that owns each page
		frappe.throw(_("The webhook is configured centrally by your provider"))
	if not settings.webhook_verify_token:
		frappe.throw(_("Save the app settings first to generate a verify token"))
	try:
		graph_post(
			f"{get_app_id()}/subscriptions",
			_app_token(),
			{
				"object": "page",
				"callback_url": get_url(WEBHOOK_PATH),
				"fields": "leadgen",
				"verify_token": settings.webhook_verify_token,
				"include_values": "true",
			},
		)
	except MetaAPIError as exc:
		frappe.throw(_("Could not configure the webhook automatically: {0}").format(exc))
	return get_webhook_subscription()


@frappe.whitelist()
def get_webhook_subscription() -> dict:
	"""Current app-level webhook subscription state, straight from Meta."""
	_check_manager()
	if not is_hub():
		return {"configured": True, "managed_by_hub": True, "callback_url": hub_url() + WEBHOOK_PATH}
	try:
		data = graph_get(f"{get_app_id()}/subscriptions", _app_token())
	except MetaAPIError as exc:
		return {"configured": False, "error": str(exc)[:300]}
	for row in data.get("data") or []:
		if row.get("object") != "page":
			continue
		fields = [f.get("name") if isinstance(f, dict) else f for f in row.get("fields") or []]
		return {
			"configured": bool(row.get("active", True)) and "leadgen" in fields,
			"callback_url": row.get("callback_url") or "",
			"fields": fields,
			"matches_site": (row.get("callback_url") or "") == get_url(WEBHOOK_PATH),
		}
	return {"configured": False}


@frappe.whitelist(methods=["POST"])
def disconnect() -> dict:
	_check_manager()
	settings = frappe.get_doc("CRM Meta Settings")
	settings.user_access_token = ""
	settings.connected_user_id = ""
	settings.connected_user_name = ""
	settings.user_token_expires_at = None
	settings.save()
	frappe.clear_document_cache("CRM Meta Settings", "CRM Meta Settings")
	return get_status()


@frappe.whitelist(methods=["POST"])
def refresh_pages() -> dict:
	"""Re-pull pages and forms with the stored long-lived user token."""
	_check_manager()
	settings = get_settings()
	token = settings.get_password("user_access_token", raise_exception=False)
	if not token:
		frappe.throw(_("Connect Facebook first"))
	try:
		pages = sync_pages_and_forms(token)
	except MetaAPIError as exc:
		frappe.throw(_("Meta API error: {0}").format(exc))
	return {"pages": len(pages)}


@frappe.whitelist()
def get_pages() -> list[dict]:
	_check_manager()
	pages = frappe.get_all(
		"Facebook Page",
		fields=[
			"name",
			"page_name",
			"category",
			"sync_enabled",
			"webhook_subscribed",
			"token_valid",
			"last_webhook_at",
		],
		order_by="page_name asc",
	)
	forms_by_page: dict[str, list] = {}
	for form in frappe.get_all(
		"Facebook Lead Form",
		fields=["name", "form_name", "form_status", "page", "last_lead_at"],
		order_by="form_name asc",
	):
		forms_by_page.setdefault(form.page, []).append(form)
	lead_counts = dict(
		frappe.get_all(
			"CRM Lead",
			filters={"facebook_form_id": ["is", "set"]},
			fields=["facebook_form_id", "count(name) as total"],
			group_by="facebook_form_id",
			as_list=True,
		)
	)
	unmapped = {}
	for row in frappe.get_all(
		"Facebook Lead Form Question",
		fields=["parent", "mapped_to_crm_field"],
	):
		if not row.mapped_to_crm_field:
			unmapped[row.parent] = unmapped.get(row.parent, 0) + 1

	for page in pages:
		page["forms"] = forms_by_page.get(page.name, [])
		for form in page["forms"]:
			form["lead_count"] = lead_counts.get(form.name, 0)
			form["unmapped_questions"] = unmapped.get(form.name, 0)
	return pages


@frappe.whitelist(methods=["POST"])
def set_page_sync(page_id: str, enabled: bool) -> dict:
	"""Enable/disable a page: subscribes (or unsubscribes) the app to the page's
	leadgen webhook with the PAGE token."""
	_check_manager()
	enabled = bool(frappe.utils.sbool(enabled))
	page = frappe.get_doc("Facebook Page", page_id)
	token = get_page_token(page_id)
	if not token:
		frappe.throw(_("No page token stored. Reconnect Facebook."))

	subscribed = page.webhook_subscribed
	try:
		if enabled:
			result = graph_post(f"{page_id}/subscribed_apps", token, {"subscribed_fields": "leadgen"})
			subscribed = 1 if result.get("success") else 0
		else:
			graph_post(f"{page_id}/subscribed_apps", token, {"method": "delete"})
			subscribed = 0
	except MetaAPIError as exc:
		if enabled:
			frappe.throw(_("Could not subscribe the page to the leadgen webhook: {0}").format(exc))
		subscribed = 0

	page.sync_enabled = 1 if enabled else 0
	page.webhook_subscribed = subscribed
	page.save(ignore_permissions=True)

	if enabled:
		# tell the hub that leads for this page belong to this site
		from crm.integrations.meta.relay import claim_page

		claim_page(page_id)
	return {"sync_enabled": page.sync_enabled, "webhook_subscribed": page.webhook_subscribed}


@frappe.whitelist()
def get_form_mapping(form_id: str) -> dict:
	_check_manager()
	form = frappe.get_doc("Facebook Lead Form", form_id)
	return {
		"name": form.name,
		"form_name": form.form_name,
		"page": form.page,
		"questions": [
			{
				"key": q.key,
				"label": q.label,
				"type": q.type,
				"mapped_to_crm_field": q.mapped_to_crm_field or "",
			}
			for q in form.questions
		],
		"lead_fields": get_lead_fields(),
	}


@frappe.whitelist(methods=["POST"])
def save_form_mapping(form_id: str, mapping: dict | str) -> None:
	"""mapping: {question_key: crm_fieldname}"""
	_check_manager()
	if isinstance(mapping, str):
		mapping = json.loads(mapping)
	valid_fields = {f["fieldname"] for f in get_lead_fields()}
	form = frappe.get_doc("Facebook Lead Form", form_id)
	for question in form.questions:
		target = (mapping.get(question.key) or "").strip()
		if target and target not in valid_fields:
			frappe.throw(_("Invalid CRM field: {0}").format(target))
		question.mapped_to_crm_field = target
	form.save(ignore_permissions=True)


def get_lead_fields() -> list[dict]:
	meta = frappe.get_meta("CRM Lead")
	mappable_types = {
		"Data",
		"Small Text",
		"Text",
		"Long Text",
		"Select",
		"Int",
		"Float",
		"Currency",
		"Date",
		"Datetime",
		"Phone",
		"Link",
	}
	skip = {"facebook_lead_id", "facebook_form_id", "naming_series"}
	return [
		{"fieldname": df.fieldname, "label": df.label or df.fieldname}
		for df in meta.fields
		if df.fieldtype in mappable_types and df.fieldname not in skip and not df.read_only
	]


@frappe.whitelist(methods=["POST"])
def backfill(form_id: str, days: int = 90) -> dict:
	"""Pull historical leads (Meta keeps them 90 days) for one form, now."""
	_check_manager()
	days = min(int(days), 90)
	since = frappe.utils.add_to_date(frappe.utils.now_datetime(), days=-days)
	if frappe.flags.in_test:
		return backfill_form(form_id, since=since)
	frappe.enqueue(
		"crm.integrations.meta.leads.backfill_form",
		queue="long",
		form_id=form_id,
		since=since,
	)
	return {"queued": True}


@frappe.whitelist()
def get_failure_logs(limit: int = 50) -> list[dict]:
	_check_manager()
	return frappe.get_all(
		"Failed Lead Sync Log",
		fields=["name", "type", "lead_data", "traceback", "creation"],
		order_by="creation desc",
		page_length=min(int(limit), 200),
	)


@frappe.whitelist()
def test_connection() -> dict:
	"""Sanity check: token valid + can list pages."""
	_check_manager()
	settings = get_settings()
	token = settings.get_password("user_access_token", raise_exception=False)
	if not token:
		frappe.throw(_("Connect Facebook first"))
	try:
		me = graph_get("me", token, {"fields": "id,name"})
		return {"ok": True, "user": me.get("name")}
	except MetaAPIError as exc:
		return {"ok": False, "error": str(exc)}


@frappe.whitelist(methods=["POST"])
def create_test_lead(form_id: str) -> dict:
	"""Create a Meta test lead for the form (1 per form; the webhook fires for it).

	Requires the app to be Live; the official Lead Ads Testing tool is the
	alternative: https://developers.facebook.com/tools/lead-ads-testing
	"""
	_check_manager()
	page = frappe.db.get_value("Facebook Lead Form", form_id, "page")
	token = get_page_token(page) if page else None
	if not token:
		frappe.throw(_("No page token stored. Reconnect Facebook."))
	try:
		result = graph_post(f"{form_id}/test_leads", token, {})
		return {"ok": True, "id": result.get("id")}
	except MetaAPIError as exc:
		frappe.throw(_("Could not create test lead: {0}").format(exc))
