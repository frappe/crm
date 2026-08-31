# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Execution engine for CRM Automation.

Step schema (the `steps` JSON field of CRM Automation is an ordered list):

    {"type": "send_email", "subject": "...", "message": "..."}
    {"type": "send_sms", "message": "..."}
    {"type": "send_whatsapp_template", "template": "..."}
    {"type": "create_task", "title": "...", "due_in_days": 2, "assigned_to": ""}
    {"type": "assign", "user": "user@x.com"}
    {"type": "add_tag_comment", "comment": "..."}
    {"type": "set_field", "field": "status", "value": "Nurture"}
    {"type": "notify", "message": "..."}
    {"type": "wait", "days": 0, "hours": 4, "minutes": 0}
    {"type": "stop_if", "condition": {"field": "...", "operator": "...", "value": ...}}

Every step accepts an optional `condition` (same schema as stop_if) — when the
record does not match, the step is skipped. Text fields (subject, message,
title, comment) support Jinja placeholders rendered against the record, e.g.
"Ciao {{ first_name }}".

Condition operators: equals, not_equals, contains, is_set, is_not_set.
"""

import json

import frappe
from frappe import _
from frappe.utils import add_to_date, get_datetime, now_datetime

EVENT_TO_TRIGGER = {
	"lead_created": "Lead Created",
	"deal_created": "Deal Created",
	"lead_status_changed": "Lead Status Changed",
	"deal_status_changed": "Deal Status Changed",
	"booking_created": "Booking Created",
	"booking_cancelled": "Booking Cancelled",
	"sms_received": "Incoming SMS",
}

REPLY_EVENTS = ("sms_received", "whatsapp_received")

STEP_TYPES = (
	"send_email",
	"send_sms",
	"send_whatsapp_template",
	"create_task",
	"assign",
	"add_tag_comment",
	"set_field",
	"notify",
	"wait",
	"stop_if",
)

CONDITION_OPERATORS = ("equals", "not_equals", "contains", "is_set", "is_not_set")


def process_event(event: str, doc) -> None:
	"""Entry point called from doc_events / feature code. Never raises."""
	if frappe.flags.in_crm_automation or frappe.flags.in_install or frappe.flags.in_migrate:
		return
	try:
		reference = resolve_reference(event, doc)
		if not reference:
			return
		ref_doctype, ref_name = reference
		if event in REPLY_EVENTS:
			exit_enrollments_on_reply(ref_doctype, ref_name)
		trigger = EVENT_TO_TRIGGER.get(event)
		if not trigger:
			return
		for automation in frappe.get_all(
			"CRM Automation", filters={"enabled": 1, "trigger_event": trigger}, pluck="name"
		):
			enroll(automation, ref_doctype, ref_name)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "CRM Automation: process_event failed")


def resolve_reference(event: str, doc) -> tuple[str, str] | None:
	"""The lead/deal an event is about — enrollments always attach to leads/deals."""
	if doc.doctype in ("CRM Lead", "CRM Deal"):
		return doc.doctype, doc.name
	if doc.doctype == "CRM Booking":
		return ("CRM Lead", doc.lead) if doc.lead else None
	if doc.doctype == "CRM SMS Message" or doc.doctype == "WhatsApp Message":
		if doc.get("reference_doctype") in ("CRM Lead", "CRM Deal") and doc.get("reference_name"):
			return doc.reference_doctype, doc.reference_name
	return None


def exit_enrollments_on_reply(ref_doctype: str, ref_name: str) -> None:
	enrollments = frappe.get_all(
		"CRM Automation Enrollment",
		filters={
			"reference_doctype": ref_doctype,
			"reference_name": ref_name,
			"status": ["in", ["Active", "Waiting"]],
		},
		fields=["name", "automation"],
	)
	for row in enrollments:
		if frappe.db.get_value("CRM Automation", row.automation, "exit_on_reply"):
			enr = frappe.get_doc("CRM Automation Enrollment", row.name)
			enr.status = "Exited"
			enr.wait_until = None
			log_step(enr, enr.current_step, "goal", "Success", _("Contact replied — exited automation"))
			enr.save(ignore_permissions=True)


def enroll(automation_name: str, ref_doctype: str, ref_name: str) -> str | None:
	automation = frappe.get_doc("CRM Automation", automation_name)

	existing_filters = {
		"automation": automation_name,
		"reference_doctype": ref_doctype,
		"reference_name": ref_name,
	}
	if automation.allow_reenrollment:
		existing_filters["status"] = ["in", ["Active", "Waiting"]]
	if frappe.db.exists("CRM Automation Enrollment", existing_filters):
		return None

	ref_doc = frappe.get_doc(ref_doctype, ref_name)
	condition = parse_json(automation.trigger_condition)
	if condition and not evaluate_condition(condition, ref_doc):
		return None

	enrollment = frappe.get_doc(
		{
			"doctype": "CRM Automation Enrollment",
			"automation": automation_name,
			"reference_doctype": ref_doctype,
			"reference_name": ref_name,
			"status": "Active",
			"current_step": 0,
		}
	)
	enrollment.insert(ignore_permissions=True)

	if frappe.flags.in_test:
		advance_enrollment(enrollment.name)
	else:
		frappe.enqueue(
			"crm.automation.engine.advance_enrollment",
			queue="short",
			enqueue_after_commit=True,
			enrollment_name=enrollment.name,
		)
	return enrollment.name


def advance_enrollment(enrollment_name: str) -> None:
	"""Run steps from the current position until done or a wait is reached."""
	enrollment = frappe.get_doc("CRM Automation Enrollment", enrollment_name)
	if enrollment.status not in ("Active", "Waiting"):
		return

	automation = frappe.get_doc("CRM Automation", enrollment.automation)
	steps = parse_json(automation.steps) or []

	if not frappe.db.exists(enrollment.reference_doctype, enrollment.reference_name):
		enrollment.status = "Exited"
		enrollment.save(ignore_permissions=True)
		return
	ref_doc = frappe.get_doc(enrollment.reference_doctype, enrollment.reference_name)

	if enrollment.status == "Waiting":
		if not enrollment.wait_until or get_datetime(enrollment.wait_until) > now_datetime():
			return
		enrollment.status = "Active"
		enrollment.wait_until = None
		enrollment.current_step += 1  # move past the satisfied wait step

	frappe.flags.in_crm_automation = True
	try:
		while enrollment.status == "Active":
			if enrollment.current_step >= len(steps):
				enrollment.status = "Completed"
				break
			step = steps[enrollment.current_step]
			step_type = step.get("type")

			condition = step.get("condition")
			if condition and not evaluate_condition(condition, ref_doc):
				log_step(enrollment, enrollment.current_step, step_type, "Skipped", _("Condition not met"))
				enrollment.current_step += 1
				continue

			if step_type == "wait":
				enrollment.wait_until = add_to_date(
					now_datetime(),
					days=int(step.get("days") or 0),
					hours=int(step.get("hours") or 0),
					minutes=int(step.get("minutes") or 0),
				)
				enrollment.status = "Waiting"
				break

			if step_type == "stop_if":
				if evaluate_condition(step.get("condition") or {}, ref_doc):
					log_step(
						enrollment, enrollment.current_step, step_type, "Success", _("Stop condition met")
					)
					enrollment.status = "Exited"
					break
				enrollment.current_step += 1
				continue

			try:
				detail = execute_step(step, ref_doc)
				log_step(enrollment, enrollment.current_step, step_type, "Success", detail)
			except Exception:
				frappe.log_error(frappe.get_traceback(), f"CRM Automation: step failed ({automation.name})")
				log_step(enrollment, enrollment.current_step, step_type, "Failed", _("See error log"))
			enrollment.current_step += 1
			ref_doc.reload()
	finally:
		frappe.flags.in_crm_automation = False

	enrollment.save(ignore_permissions=True)


def process_due_enrollments() -> None:
	"""Scheduler tick: resume enrollments whose wait has elapsed."""
	due = frappe.get_all(
		"CRM Automation Enrollment",
		filters={"status": "Waiting", "wait_until": ["<=", now_datetime()]},
		pluck="name",
		limit=200,
	)
	for name in due:
		try:
			advance_enrollment(name)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), "CRM Automation: scheduler advance failed")


# --- step execution --------------------------------------------------------


def execute_step(step: dict, ref_doc) -> str:
	step_type = step.get("type")
	handler = {
		"send_email": step_send_email,
		"send_sms": step_send_sms,
		"send_whatsapp_template": step_send_whatsapp_template,
		"create_task": step_create_task,
		"assign": step_assign,
		"add_tag_comment": step_add_comment,
		"set_field": step_set_field,
		"notify": step_notify,
	}.get(step_type)
	if not handler:
		frappe.throw(_("Unknown step type: {0}").format(step_type))
	return handler(step, ref_doc)


def render(text: str, ref_doc) -> str:
	if not text:
		return ""
	return frappe.render_template(text, ref_doc.as_dict())


def step_send_email(step, ref_doc) -> str:
	recipient = ref_doc.get("email")
	if not recipient:
		return _("Skipped: record has no email")
	frappe.sendmail(
		recipients=[recipient],
		subject=render(step.get("subject") or _("Message from {0}").format(frappe.local.site), ref_doc),
		message=render(step.get("message") or "", ref_doc),
		reference_doctype=ref_doc.doctype,
		reference_name=ref_doc.name,
	)
	return _("Email queued to {0}").format(recipient)


def step_send_sms(step, ref_doc) -> str:
	from crm.api.sms import send_automation_sms

	number = ref_doc.get("mobile_no") or ref_doc.get("phone")
	if not number:
		return _("Skipped: record has no phone number")
	ok = send_automation_sms(
		to=number,
		message=render(step.get("message") or "", ref_doc),
		reference_doctype=ref_doc.doctype,
		reference_name=ref_doc.name,
	)
	return _("SMS sent to {0}").format(number) if ok else _("SMS send failed (see error log)")


def step_send_whatsapp_template(step, ref_doc) -> str:
	if not frappe.db.exists("DocType", "WhatsApp Message"):
		return _("Skipped: WhatsApp app is not installed")
	number = ref_doc.get("mobile_no") or ref_doc.get("phone")
	if not number:
		return _("Skipped: record has no phone number")
	from crm.api.whatsapp import send_whatsapp_template

	send_whatsapp_template(
		reference_doctype=ref_doc.doctype,
		reference_name=ref_doc.name,
		template=step.get("template"),
		to=number,
	)
	return _("WhatsApp template {0} sent to {1}").format(step.get("template"), number)


def step_create_task(step, ref_doc) -> str:
	task = frappe.get_doc(
		{
			"doctype": "CRM Task",
			"title": render(step.get("title") or _("Follow up"), ref_doc),
			"assigned_to": step.get("assigned_to") or ref_doc.get("lead_owner") or ref_doc.get("deal_owner"),
			"due_date": add_to_date(now_datetime(), days=int(step.get("due_in_days") or 0)),
			"reference_doctype": ref_doc.doctype,
			"reference_docname": ref_doc.name,
		}
	)
	task.insert(ignore_permissions=True)
	return _("Task {0} created").format(task.name)


def step_assign(step, ref_doc) -> str:
	user = step.get("user")
	if not user or not frappe.db.exists("User", user):
		return _("Skipped: no valid user to assign")
	from frappe.desk.form import assign_to

	try:
		assign_to.add(
			{
				"assign_to": [user],
				"doctype": ref_doc.doctype,
				"name": ref_doc.name,
				"description": _("Assigned by automation"),
			},
			ignore_permissions=True,
		)
	except assign_to.DuplicateToDoError:
		return _("Skipped: already assigned to {0}").format(user)
	return _("Assigned to {0}").format(user)


def step_add_comment(step, ref_doc) -> str:
	ref_doc.add_comment("Comment", render(step.get("comment") or "", ref_doc))
	return _("Comment added")


def step_set_field(step, ref_doc) -> str:
	field = step.get("field")
	if not field or not ref_doc.meta.get_field(field):
		frappe.throw(_("Invalid field: {0}").format(field))
	ref_doc.set(field, step.get("value"))
	ref_doc.save(ignore_permissions=True)
	return _("{0} set to {1}").format(field, step.get("value"))


def step_notify(step, ref_doc) -> str:
	from crm.api.doc import get_assigned_users
	from crm.fcrm.doctype.crm_notification.crm_notification import notify_user

	message = render(step.get("message") or "", ref_doc)
	users = get_assigned_users(ref_doc.doctype, ref_doc.name) or []
	owner = ref_doc.get("lead_owner") or ref_doc.get("deal_owner")
	if owner and owner not in users:
		users.append(owner)
	safe_message = frappe.utils.escape_html(message)
	for user in users:
		notify_user(
			{
				"owner": frappe.session.user,
				"assigned_to": user,
				"notification_type": "Assignment",
				"message": message,
				"notification_text": f'<div class="mb-2 leading-5 text-ink-gray-5">{safe_message}</div>',
				"reference_doctype": ref_doc.doctype,
				"reference_docname": ref_doc.name,
				"redirect_to_doctype": ref_doc.doctype,
				"redirect_to_docname": ref_doc.name,
			}
		)
	return _("Notified {0} user(s)").format(len(users))


# --- helpers ---------------------------------------------------------------


def parse_json(value):
	if not value:
		return None
	if isinstance(value, (list, dict)):
		return value
	try:
		return json.loads(value)
	except (ValueError, TypeError):
		return None


def evaluate_condition(condition: dict, ref_doc) -> bool:
	field = condition.get("field")
	operator = condition.get("operator") or "equals"
	expected = condition.get("value")
	actual = ref_doc.get(field) if field else None

	if operator == "equals":
		return str(actual) == str(expected)
	if operator == "not_equals":
		return str(actual) != str(expected)
	if operator == "contains":
		return expected is not None and str(expected).lower() in str(actual or "").lower()
	if operator == "is_set":
		return bool(actual)
	if operator == "is_not_set":
		return not actual
	return False


def log_step(enrollment, step_index: int, action: str, status: str, detail: str = "") -> None:
	enrollment.append(
		"logs",
		{"step_index": step_index, "action": action or "", "status": status, "detail": (detail or "")[:500]},
	)


def validate_steps(steps) -> None:
	"""Shared validation used by the CRM Automation controller and the API."""
	if not isinstance(steps, list) or not steps:
		frappe.throw(_("Steps must be a non-empty list"))
	for i, step in enumerate(steps):
		if not isinstance(step, dict) or step.get("type") not in STEP_TYPES:
			frappe.throw(_("Step {0}: unknown type {1}").format(i + 1, (step or {}).get("type")))
		if step.get("type") == "wait":
			total = (
				int(step.get("days") or 0) * 1440
				+ int(step.get("hours") or 0) * 60
				+ int(step.get("minutes") or 0)
			)
			if total <= 0:
				frappe.throw(_("Step {0}: wait must have a positive duration").format(i + 1))
		for cond_key in ("condition",):
			cond = step.get(cond_key)
			if cond and (cond.get("operator") or "equals") not in CONDITION_OPERATORS:
				frappe.throw(_("Step {0}: unknown condition operator").format(i + 1))
		if step.get("type") == "stop_if" and not step.get("condition"):
			frappe.throw(_("Step {0}: stop_if requires a condition").format(i + 1))


# --- doc_events glue -------------------------------------------------------


def _status_actually_changed(doc) -> bool:
	# get_doc_before_save is absent on insert, so this stays False for new docs
	# (has_value_changed would report True there)
	previous = doc.get_doc_before_save()
	return bool(previous) and previous.get("status") != doc.get("status")


def on_lead_created(doc, method=None):
	process_event("lead_created", doc)


def on_lead_updated(doc, method=None):
	if _status_actually_changed(doc):
		process_event("lead_status_changed", doc)


def on_deal_created(doc, method=None):
	process_event("deal_created", doc)


def on_deal_updated(doc, method=None):
	if _status_actually_changed(doc):
		process_event("deal_status_changed", doc)


def on_whatsapp_received(doc, method=None):
	if doc.get("type") == "Incoming":
		process_event("whatsapp_received", doc)


def on_booking_created(doc, method=None):
	process_event("booking_created", doc)


def on_booking_updated(doc, method=None):
	if _status_actually_changed(doc) and doc.status == "Cancelled":
		process_event("booking_cancelled", doc)
