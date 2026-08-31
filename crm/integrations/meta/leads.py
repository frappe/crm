# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Lead ingestion shared by the real-time webhook and the polling backfill.

Deduplication is by Meta's lead id (`facebook_lead_id`) — the id is globally
unique, which makes webhook + backfill safely idempotent. Facebook keeps lead
data for 90 days only, so the backfill can never recover older leads.
"""

import frappe
from frappe import _

from crm.integrations.meta.client import MetaAPIError, graph_get, graph_get_paginated

# documented lead-node fields; PLATFORM_FIELDS adds `platform` (fb/ig) which is
# not guaranteed on every Graph version — we retry without it on error 100
LEAD_FIELDS = "id,created_time,ad_id,form_id,is_organic,field_data"
LEAD_FIELDS_WITH_PLATFORM = LEAD_FIELDS + ",platform"


def fetch_lead(leadgen_id: str, token: str) -> dict:
	try:
		return graph_get(leadgen_id, token, {"fields": LEAD_FIELDS_WITH_PLATFORM})
	except MetaAPIError as exc:
		if exc.code == 100:  # invalid field on this version
			return graph_get(leadgen_id, token, {"fields": LEAD_FIELDS})
		raise


def get_page_token(page_id: str) -> str | None:
	if not frappe.db.exists("Facebook Page", page_id):
		return None
	return frappe.get_doc("Facebook Page", page_id).get_password("access_token", raise_exception=False)


def ingest_leadgen_entry(
	leadgen_id: str, page_id: str | None = None, form_id: str | None = None, created_time=None
) -> None:
	"""Webhook path: fetch one lead by id and store it."""
	if not leadgen_id:
		return
	if page_id and not frappe.db.get_value("Facebook Page", page_id, "sync_enabled"):
		return

	token = get_page_token(page_id) if page_id else None
	if not token and form_id:
		page = frappe.db.get_value("Facebook Lead Form", form_id, "page")
		token = get_page_token(page) if page else None
	if not token:
		_log_failure({"leadgen_id": leadgen_id}, form_id, _("No page token available"))
		return

	if page_id:
		frappe.db.set_value(
			"Facebook Page", page_id, "last_webhook_at", frappe.utils.now(), update_modified=False
		)

	try:
		lead = fetch_lead(leadgen_id, token)
	except MetaAPIError as exc:
		_log_failure({"leadgen_id": leadgen_id}, form_id, str(exc))
		return
	store_lead(lead, lead.get("form_id") or form_id)


def backfill_form(form_id: str, since=None, page_token: str | None = None) -> dict:
	"""Polling path: fetch all (remaining) leads of a form, paginated."""
	token = page_token
	if not token:
		page = frappe.db.get_value("Facebook Lead Form", form_id, "page")
		token = get_page_token(page) if page else None
	if not token:
		frappe.throw(_("No page token available for this form. Reconnect Facebook."))

	params = {"fields": LEAD_FIELDS}  # keep the safe set for bulk reads
	if since:
		params["filtering"] = frappe.as_json(
			[
				{
					"field": "time_created",
					"operator": "GREATER_THAN",
					"value": int(frappe.utils.data.get_timestamp(since)),
				}
			]
		)

	created, skipped, failed = 0, 0, 0
	for lead in graph_get_paginated(f"{form_id}/leads", token, params, max_pages=200):
		result = store_lead(lead, form_id)
		if result == "created":
			created += 1
		elif result == "duplicate":
			skipped += 1
		else:
			failed += 1
	return {"created": created, "duplicates": skipped, "failed": failed}


def store_lead(lead: dict, form_id: str | None) -> str:
	"""Map field_data → CRM Lead via the form's question mapping. Idempotent."""
	lead_id = lead.get("id")
	if not lead_id:
		return "failed"
	if frappe.db.exists("CRM Lead", {"facebook_lead_id": lead_id}):
		return "duplicate"

	mapping = get_question_mapping(form_id)
	values: dict = {}
	for item in lead.get("field_data") or []:
		crm_field = mapping.get(item.get("name"))
		raw_values = item.get("values") or []
		if not crm_field or not raw_values:
			continue
		values[crm_field] = normalize_value(crm_field, raw_values[0])

	if "first_name" not in values:
		# FULL_NAME questions arrive under one key: split into first/last
		full = values.pop("full_name", None) or next(
			(
				(item.get("values") or [""])[0]
				for item in lead.get("field_data") or []
				if item.get("name") in ("full_name", "FULL_NAME")
			),
			None,
		)
		if full:
			parts = str(full).split(maxsplit=1)
			values["first_name"] = parts[0]
			values.setdefault("last_name", parts[1] if len(parts) > 1 else "")

	if not values.get("first_name"):
		_log_failure(lead, form_id, _("No first name could be mapped"))
		return "failed"

	values.update(
		{
			"doctype": "CRM Lead",
			"source": _ensure_source("Instagram" if lead.get("platform") == "ig" else "Facebook"),
			"facebook_lead_id": lead_id,
			"facebook_form_id": form_id,
		}
	)
	try:
		frappe.get_doc(values).insert(ignore_permissions=True)
		if form_id:
			frappe.db.set_value(
				"Facebook Lead Form", form_id, "last_lead_at", frappe.utils.now(), update_modified=False
			)
		return "created"
	except frappe.UniqueValidationError:
		return "duplicate"
	except Exception:
		_log_failure(lead, form_id, frappe.get_traceback())
		return "failed"


def get_question_mapping(form_id: str | None) -> dict:
	if not form_id:
		return {}
	rows = frappe.get_all(
		"Facebook Lead Form Question",
		filters={"parent": form_id},
		fields=["key", "mapped_to_crm_field"],
	)
	return {row.key: row.mapped_to_crm_field for row in rows if row.mapped_to_crm_field}


def normalize_value(crm_field: str, value):
	value = str(value).strip()
	if crm_field in ("mobile_no", "phone"):
		# Meta sends phones like "+3933312345 67" / "p:+39..." — keep digits and +
		value = value.removeprefix("p:")
		value = "+" + "".join(ch for ch in value if ch.isdigit()) if value.startswith("+") else value
	return value


def _ensure_source(source_name: str) -> str:
	if not frappe.db.exists("CRM Lead Source", source_name):
		frappe.get_doc({"doctype": "CRM Lead Source", "source_name": source_name}).insert(
			ignore_permissions=True
		)
	return source_name


def _log_failure(lead_data: dict, form_id: str | None, traceback: str):
	try:
		source = frappe.db.get_value("Lead Sync Source", {"facebook_lead_form": form_id}) if form_id else None
		frappe.get_doc(
			{
				"doctype": "Failed Lead Sync Log",
				"type": "Failure",
				"lead_data": frappe.as_json(lead_data),
				"source": source,
				"traceback": traceback,
			}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Meta: failed to write failure log")


# --- hourly reconciliation --------------------------------------------------


def reconcile_synced_pages() -> None:
	"""Hourly safety net: Meta retries failed webhooks for only 36 hours, so we
	re-poll the last 2 days of every synced page's forms (dedup makes it cheap)."""
	since = frappe.utils.add_to_date(frappe.utils.now_datetime(), days=-2)
	pages = frappe.get_all("Facebook Page", filters={"sync_enabled": 1}, pluck="name")
	if not pages:
		return
	forms = frappe.get_all("Facebook Lead Form", filters={"page": ["in", pages]}, pluck="name")
	for form_id in forms:
		try:
			backfill_form(form_id, since=since)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), f"Meta: reconciliation failed for form {form_id}")


# --- daily token health -----------------------------------------------------


def check_token_health() -> None:
	"""Daily: verify page tokens still work; flag pages and notify managers."""
	from crm.integrations.meta.client import debug_token

	settings = frappe.get_cached_doc("CRM Meta Settings")
	if not settings.app_id:
		return
	broken = []
	for page in frappe.get_all("Facebook Page", filters={"sync_enabled": 1}, pluck="name"):
		token = get_page_token(page)
		valid = False
		if token:
			try:
				valid = bool(debug_token(token).get("is_valid"))
			except Exception:
				valid = False
		frappe.db.set_value("Facebook Page", page, "token_valid", 1 if valid else 0, update_modified=False)
		if not valid:
			broken.append(page)
	if broken:
		frappe.log_error(
			f"Meta pages with invalid tokens: {', '.join(broken)}. Reconnect Facebook from Settings.",
			"Meta Lead Ads: token expired",
		)
