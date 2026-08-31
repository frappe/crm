import json

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit

from crm.automation.engine import STEP_TYPES, parse_json, validate_steps

MANAGER_ROLES = {"System Manager", "Sales Manager"}


def _check_manager():
	if not MANAGER_ROLES & set(frappe.get_roles()):
		frappe.throw(_("Only sales managers can manage automations"), frappe.PermissionError)


@frappe.whitelist()
def list_automations() -> list[dict]:
	automations = frappe.get_list(
		"CRM Automation",
		fields=["name", "title", "enabled", "trigger_event", "description", "modified"],
		order_by="modified desc",
	)
	counts = dict(
		frappe.get_all(
			"CRM Automation Enrollment",
			fields=["automation", "count(name) as total"],
			group_by="automation",
			as_list=True,
		)
	)
	active = dict(
		frappe.get_all(
			"CRM Automation Enrollment",
			filters={"status": ["in", ["Active", "Waiting"]]},
			fields=["automation", "count(name) as total"],
			group_by="automation",
			as_list=True,
		)
	)
	for row in automations:
		row["enrolled_count"] = counts.get(row.name, 0)
		row["active_count"] = active.get(row.name, 0)
	return automations


@frappe.whitelist()
def get_automation(name: str) -> dict:
	doc = frappe.get_doc("CRM Automation", name)
	doc.check_permission("read")
	return {
		"name": doc.name,
		"title": doc.title,
		"enabled": doc.enabled,
		"trigger_event": doc.trigger_event,
		"trigger_condition": parse_json(doc.trigger_condition),
		"allow_reenrollment": doc.allow_reenrollment,
		"exit_on_reply": doc.exit_on_reply,
		"description": doc.description or "",
		"steps": parse_json(doc.steps) or [],
		"trigger_config": parse_json(doc.trigger_config),
		"webhook_key": doc.webhook_key or "",
		"time_window_enabled": doc.time_window_enabled,
		"window_start": str(doc.window_start or ""),
		"window_end": str(doc.window_end or ""),
		"window_days": parse_json(doc.window_days) or [],
	}


@frappe.whitelist(methods=["POST"])
def save_automation(automation: dict | str, name: str | None = None) -> dict:
	"""Create or update an automation from the visual builder payload."""
	_check_manager()
	if isinstance(automation, str):
		automation = json.loads(automation)

	steps = automation.get("steps") or []
	validate_steps(steps)

	values = {
		"title": (automation.get("title") or "").strip(),
		"trigger_event": automation.get("trigger_event"),
		"trigger_condition": json.dumps(automation.get("trigger_condition") or None),
		"allow_reenrollment": 1 if automation.get("allow_reenrollment") else 0,
		"exit_on_reply": 1 if automation.get("exit_on_reply") else 0,
		"description": automation.get("description") or "",
		"steps": json.dumps(steps),
		"trigger_config": json.dumps(automation.get("trigger_config") or None),
		"time_window_enabled": 1 if automation.get("time_window_enabled") else 0,
		"window_start": automation.get("window_start") or None,
		"window_end": automation.get("window_end") or None,
		"window_days": json.dumps(automation.get("window_days") or []),
	}
	if not values["title"]:
		frappe.throw(_("Title is required"))

	if name:
		doc = frappe.get_doc("CRM Automation", name)
		doc.update(values)
		doc.save()
	else:
		doc = frappe.get_doc({"doctype": "CRM Automation", "enabled": 0, **values})
		doc.insert()
	return get_automation(doc.name)


@frappe.whitelist(methods=["POST"])
def toggle_automation(name: str, enabled: bool) -> dict:
	_check_manager()
	doc = frappe.get_doc("CRM Automation", name)
	doc.enabled = 1 if frappe.utils.sbool(enabled) else 0
	doc.save()
	return {"name": doc.name, "enabled": doc.enabled}


@frappe.whitelist(methods=["POST"])
def delete_automation(name: str) -> None:
	_check_manager()
	frappe.delete_doc("CRM Automation", name)


@frappe.whitelist()
def get_enrollments(automation: str, limit: int = 50) -> list[dict]:
	rows = frappe.get_list(
		"CRM Automation Enrollment",
		filters={"automation": automation},
		fields=[
			"name",
			"reference_doctype",
			"reference_name",
			"status",
			"current_step",
			"wait_until",
			"modified",
		],
		order_by="modified desc",
		page_length=min(int(limit), 200),
	)
	return rows


@frappe.whitelist()
def get_builder_meta() -> dict:
	"""Static metadata the visual builder needs (step palette, triggers, templates)."""
	from crm.automation.engine import CONDITION_OPERATORS, GOAL_EVENTS, TRIGGER_EVENTS, WAIT_MODES

	email_templates = []
	if frappe.db.exists("DocType", "Email Template"):
		email_templates = frappe.get_all("Email Template", pluck="name", limit=100)
	whatsapp_templates = []
	if frappe.db.exists("DocType", "WhatsApp Templates"):
		whatsapp_templates = frappe.get_all("WhatsApp Templates", pluck="name", limit=100)
	sales_users = frappe.get_all(
		"Has Role",
		filters={"role": ["in", ["Sales User", "Sales Manager"]], "parenttype": "User"},
		pluck="parent",
		distinct=True,
	)
	return {
		"step_types": list(STEP_TYPES),
		"trigger_events": TRIGGER_EVENTS,
		"condition_operators": list(CONDITION_OPERATORS),
		"goal_events": list(GOAL_EVENTS),
		"wait_modes": list(WAIT_MODES),
		"email_templates": email_templates,
		"whatsapp_templates": whatsapp_templates,
		"tracked_links": frappe.get_all("CRM Tracked Link", pluck="name", limit=100),
		"automations": frappe.get_all("CRM Automation", pluck="name", limit=200),
		"users": sorted(set(sales_users)),
		"lead_statuses": frappe.get_all("CRM Lead Status", pluck="name", order_by="position asc"),
		"deal_statuses": frappe.get_all("CRM Deal Status", pluck="name", order_by="position asc"),
	}


@frappe.whitelist(methods=["POST"])
def save_settings(name: str, settings: dict | str) -> None:
	"""Workflow-level settings panel (time window, trigger config)."""
	_check_manager()
	if isinstance(settings, str):
		settings = json.loads(settings)
	doc = frappe.get_doc("CRM Automation", name)
	for field in (
		"trigger_config",
		"time_window_enabled",
		"window_start",
		"window_end",
		"window_days",
	):
		if field in settings:
			value = settings[field]
			if field in ("trigger_config", "window_days") and not isinstance(value, str):
				value = json.dumps(value)
			doc.set(field, value)
	doc.save()


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=300, seconds=60 * 60)
def inbound_webhook(automation: str, key: str) -> dict:
	"""GHL 'Inbound Webhook' trigger: external systems POST here to enroll a contact.

	URL: /api/method/crm.api.automation.inbound_webhook?automation=<name>&key=<webhook_key>
	Body: JSON with at least email or mobile_no; extra keys become the event payload.
	"""
	import hmac as hmac_mod

	doc = frappe.get_doc("CRM Automation", automation)
	if (
		doc.trigger_event != "Inbound Webhook"
		or not doc.enabled
		or not doc.webhook_key
		or not hmac_mod.compare_digest(str(key), str(doc.webhook_key))
	):
		frappe.throw(_("Invalid webhook"), frappe.PermissionError)

	payload = {}
	if frappe.request and frappe.request.data:
		try:
			payload = json.loads(frappe.request.data)
		except ValueError:
			payload = {}
	payload = {
		**{k: v for k, v in frappe.local.form_dict.items() if k not in ("automation", "key", "cmd")},
		**payload,
	}

	email = (payload.get("email") or "").strip()
	phone = (payload.get("mobile_no") or payload.get("phone") or "").strip()
	if not email and not phone:
		frappe.throw(_("Payload must contain email or mobile_no"))

	lead = None
	if email:
		lead = frappe.db.get_value("CRM Lead", {"email": email, "converted": 0})
	if not lead and phone:
		lead = frappe.db.get_value("CRM Lead", {"mobile_no": phone, "converted": 0})
	if not lead:
		from crm.api.form import _default_status

		lead_doc = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": payload.get("first_name") or email or phone,
				"last_name": payload.get("last_name") or "",
				"email": email,
				"mobile_no": phone,
				"status": _default_status("CRM Lead"),
			}
		)
		lead_doc.insert(ignore_permissions=True)
		lead = lead_doc.name

	from crm.automation.engine import process_event

	ref = frappe.get_doc("CRM Lead", lead)
	process_event("inbound_webhook", ref, payload)
	return {"lead": lead}
