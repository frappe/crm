import json

import frappe
from frappe import _

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
		"trigger_events": [
			"Lead Created",
			"Deal Created",
			"Lead Status Changed",
			"Deal Status Changed",
			"Booking Created",
			"Booking Cancelled",
			"Incoming SMS",
		],
		"condition_operators": ["equals", "not_equals", "contains", "is_set", "is_not_set"],
		"email_templates": email_templates,
		"whatsapp_templates": whatsapp_templates,
		"users": sorted(set(sales_users)),
		"lead_statuses": frappe.get_all("CRM Lead Status", pluck="name", order_by="position asc"),
		"deal_statuses": frappe.get_all("CRM Deal Status", pluck="name", order_by="position asc"),
	}
