# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Execution engine for CRM Automation — GHL-Workflows-aligned.

The builder saves a NESTED step tree (`steps` JSON on CRM Automation); on save
it is COMPILED into a flat program (`compiled_steps`) of ops with jump targets.
Enrollments carry an integer program counter plus a small JSON `state`
(split assignments, wait context), which keeps the runtime and the scheduler
simple and idempotent.

Builder step schema (ordered list; every step may carry "label" for go_to and
"condition"/"condition_groups" gating the single step):

  Communication:
    {"type": "send_email", "subject", "message", "email_template"?}
    {"type": "send_sms", "message"}
    {"type": "send_whatsapp_template", "template"}
    {"type": "notify", "message"}
  CRM:
    {"type": "create_task", "title", "due_in_days", "assigned_to"?}
    {"type": "assign", "users": [..], "only_if_unassigned": bool}   # equal round robin
    {"type": "add_note", "comment"}          (alias: add_tag_comment)
    {"type": "add_tag", "tag"} / {"type": "remove_tag", "tag"}
    {"type": "set_field", "field", "value"}
    {"type": "convert_to_deal"}              # leads only
  Data:
    {"type": "webhook", "url", "method"?, "headers"?, "body"?}
  Control flow:
    {"type": "wait", "mode": "duration", "days", "hours", "minutes"}
    {"type": "wait", "mode": "until_time", "time": "09:00", "weekdays": [..]?}
    {"type": "wait", "mode": "until_reply", "timeout_hours"?}
    {"type": "wait", "mode": "until_link_click", "link", "timeout_hours"?}
    {"type": "if_else", "branches": [{"label", "condition_groups", "steps"}...],
                         "else_steps": [...]}
    {"type": "split", "paths": [{"label", "percent", "steps"}...]}   # sticky
    {"type": "goal", "event", "value"?, "outcome": "continue|end|wait"}
    {"type": "go_to", "target": "<label>"}
    {"type": "exit"}
    {"type": "stop_if", "condition"|"condition_groups"}
    {"type": "add_to_workflow", "automation"}
    {"type": "remove_from_workflow", "automation"|"all"}

Conditions: a group is a list of {field, operator, value} ANDed together;
`condition_groups` is a list of groups ORed together (GHL segments). The single
`condition` form is treated as one group of one. Operators: equals, not_equals,
contains, is_set, is_not_set, greater_than, less_than.

Text fields render Jinja against the record: "Ciao {{ first_name }}"; tracked
links via {{ tracked_link("slug") }}.
"""

import json
import random

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
	"booking_no_show": "Booking No Show",
	"booking_completed": "Booking Completed",
	"sms_received": "Incoming SMS",
	"reply_received": "Customer Replied",
	"email_opened": "Email Opened",
	"link_clicked": "Trigger Link Clicked",
	"tag_added": "Tag Added",
	"tag_removed": "Tag Removed",
	"task_completed": "Task Completed",
	"note_added": "Note Added",
	"date_reminder": "Date Reminder",
	"inbound_webhook": "Inbound Webhook",
}

TRIGGER_EVENTS = list(EVENT_TO_TRIGGER.values())

REPLY_EVENTS = ("sms_received", "whatsapp_received", "email_replied")

ACTION_TYPES = (
	"send_email",
	"send_sms",
	"send_whatsapp_template",
	"notify",
	"create_task",
	"assign",
	"add_note",
	"add_tag_comment",  # legacy alias of add_note
	"add_tag",
	"remove_tag",
	"set_field",
	"convert_to_deal",
	"webhook",
	"add_to_workflow",
	"remove_from_workflow",
)

CONTROL_TYPES = ("wait", "if_else", "split", "goal", "go_to", "exit", "stop_if")

STEP_TYPES = ACTION_TYPES + CONTROL_TYPES

COMMUNICATION_TYPES = ("send_email", "send_sms", "send_whatsapp_template")

CONDITION_OPERATORS = (
	"equals",
	"not_equals",
	"contains",
	"is_set",
	"is_not_set",
	"greater_than",
	"less_than",
)

GOAL_EVENTS = ("reply", "link_clicked", "tag_added", "status_is", "booking_booked")

WAIT_MODES = ("duration", "until_time", "until_reply", "until_link_click")

MAX_OPS_PER_ADVANCE = 100  # go_to loop guard


# ---------------------------------------------------------------------------
# events → enrollment
# ---------------------------------------------------------------------------


def process_event(event: str, doc, payload: dict | None = None) -> None:
	"""Entry point called from doc_events / feature code. Never raises."""
	if frappe.flags.in_crm_automation or frappe.flags.in_install or frappe.flags.in_migrate:
		return
	try:
		payload = payload or {}
		reference = resolve_reference(event, doc)
		if not reference:
			return
		ref_doctype, ref_name = reference

		if event in REPLY_EVENTS:
			handle_event_for_waiters("reply", ref_doctype, ref_name, payload)
			handle_goal_event("reply", ref_doctype, ref_name, payload)
			exit_enrollments_on_reply(ref_doctype, ref_name)
		if event == "link_clicked":
			payload.setdefault("link", frappe.local.form_dict.get("_tracked_link"))
			handle_event_for_waiters("link_clicked", ref_doctype, ref_name, payload)
			handle_goal_event("link_clicked", ref_doctype, ref_name, payload)
		if event == "tag_added":
			handle_goal_event("tag_added", ref_doctype, ref_name, payload)
		if event in ("booking_created",):
			handle_goal_event("booking_booked", ref_doctype, ref_name, payload)
		if event in ("lead_status_changed", "deal_status_changed"):
			handle_goal_event("status_is", ref_doctype, ref_name, {"value": doc.get("status")})

		trigger = EVENT_TO_TRIGGER.get(event)
		if event in REPLY_EVENTS:
			trigger = "Customer Replied"
		if not trigger:
			return
		triggers = [trigger]
		if event == "sms_received":
			triggers.append("Incoming SMS")
		for automation in frappe.get_all(
			"CRM Automation", filters={"enabled": 1, "trigger_event": ["in", triggers]}, pluck="name"
		):
			enroll(automation, ref_doctype, ref_name, payload)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "CRM Automation: process_event failed")


def resolve_reference(event: str, doc) -> tuple[str, str] | None:
	"""The lead/deal an event is about — enrollments always attach to leads/deals."""
	if doc.doctype in ("CRM Lead", "CRM Deal"):
		return doc.doctype, doc.name
	if doc.doctype == "CRM Booking":
		return ("CRM Lead", doc.lead) if doc.lead else None
	if doc.doctype in ("CRM SMS Message", "WhatsApp Message", "Communication"):
		if doc.get("reference_doctype") in ("CRM Lead", "CRM Deal") and doc.get("reference_name"):
			return doc.reference_doctype, doc.reference_name
	if doc.doctype in ("CRM Task", "FCRM Note"):
		ref_dt = doc.get("reference_doctype")
		ref_dn = doc.get("reference_docname")
		if ref_dt in ("CRM Lead", "CRM Deal") and ref_dn:
			return ref_dt, ref_dn
	return None


def trigger_config_matches(automation, payload: dict) -> bool:
	"""Event-payload filters, GHL-style (which link, which tag, which form…)."""
	config = parse_json(automation.get("trigger_config")) or {}
	for key, expected in config.items():
		if expected in (None, "", []):
			continue
		actual = payload.get(key)
		if isinstance(expected, list):
			if actual not in expected:
				return False
		elif str(actual or "") != str(expected):
			return False
	return True


def exit_enrollments_on_reply(ref_doctype: str, ref_name: str) -> None:
	"""GHL 'Stop on Response' — automations flagged exit_on_reply."""
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
			if (get_state(enr).get("waiting_for") or {}).get("kind") == "reply":
				continue  # an explicit wait-for-reply wins over stop-on-response
			enr.status = "Exited"
			enr.wait_until = None
			log_step(enr, enr.current_step, "goal", "Success", _("Contact replied — exited automation"))
			enr.save(ignore_permissions=True)


def enroll(automation_name: str, ref_doctype: str, ref_name: str, payload: dict | None = None) -> str | None:
	automation = frappe.get_doc("CRM Automation", automation_name)
	if not trigger_config_matches(automation, payload or {}):
		return None

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
	groups = condition_groups_of(automation.as_dict())
	if groups and not evaluate_condition_groups(groups, ref_doc):
		return None

	enrollment = frappe.get_doc(
		{
			"doctype": "CRM Automation Enrollment",
			"automation": automation_name,
			"reference_doctype": ref_doctype,
			"reference_name": ref_name,
			"status": "Active",
			"current_step": 0,
			"state": json.dumps({"payload": payload or {}}),
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


# ---------------------------------------------------------------------------
# compiler: nested builder steps → flat program
# ---------------------------------------------------------------------------


def compile_steps(steps: list) -> list[dict]:
	"""Flatten the nested step tree into ops with resolved jump targets."""
	program: list[dict] = []
	labels: dict[str, int] = {}
	pending_jumps: list[tuple[int, str]] = []  # (op index, target label)

	def emit(op: dict, label: str | None = None) -> int:
		program.append(op)
		index = len(program) - 1
		if label:
			labels[label] = index
		return index

	def compile_block(block: list):
		for step in block or []:
			step_type = step.get("type")
			label = step.get("label")
			gate = condition_groups_of(step)

			if step_type == "if_else":
				compile_if_else(step, label)
			elif step_type == "split":
				compile_split(step, label)
			elif step_type == "wait":
				emit({"op": "wait", "step": step}, label)
			elif step_type == "goal":
				emit({"op": "goal", "step": step}, label)
			elif step_type == "go_to":
				index = emit({"op": "jump", "to": None}, label)
				pending_jumps.append((index, step.get("target")))
			elif step_type == "exit":
				emit({"op": "exit"}, label)
			elif step_type == "stop_if":
				emit({"op": "stop_if", "groups": condition_groups_of(step)}, label)
			else:  # plain action
				emit({"op": "action", "step": step, "gate": gate}, label)

	def compile_if_else(step, label):
		branches = step.get("branches") or []
		end_jumps = []
		anchor = None
		for branch in branches:
			test_index = emit(
				{"op": "branch", "groups": condition_groups_of(branch), "else_to": None},
				label if anchor is None else None,
			)
			anchor = anchor or test_index
			compile_block(branch.get("steps"))
			end_jumps.append(emit({"op": "jump", "to": None}))
			program[test_index]["else_to"] = len(program)
		compile_block(step.get("else_steps"))
		end = len(program)
		for j in end_jumps:
			program[j]["to"] = end

	def compile_split(step, label):
		paths = step.get("paths") or []
		split_index = emit({"op": "split", "paths": []}, label)
		end_jumps = []
		for path in paths:
			start = len(program)
			program[split_index]["paths"].append(
				{"label": path.get("label") or "", "percent": float(path.get("percent") or 0), "to": start}
			)
			compile_block(path.get("steps"))
			end_jumps.append(emit({"op": "jump", "to": None}))
		end = len(program)
		for j in end_jumps:
			program[j]["to"] = end

	compile_block(steps)
	emit({"op": "end"})

	for index, target in pending_jumps:
		if target not in labels:
			frappe.throw(_("go_to target not found: {0}").format(target))
		program[index]["to"] = labels[target]
	return program


# ---------------------------------------------------------------------------
# runtime
# ---------------------------------------------------------------------------


def get_state(enrollment) -> dict:
	return parse_json(enrollment.get("state")) or {}


def set_state(enrollment, state: dict) -> None:
	enrollment.state = json.dumps(state)


def advance_enrollment(enrollment_name: str, wait_result: str | None = None) -> None:
	"""Run ops from the program counter until done or a wait is reached."""
	enrollment = frappe.get_doc("CRM Automation Enrollment", enrollment_name)
	if enrollment.status not in ("Active", "Waiting"):
		return

	automation = frappe.get_doc("CRM Automation", enrollment.automation)
	program = parse_json(automation.compiled_steps) or compile_steps(parse_json(automation.steps) or [])

	if not frappe.db.exists(enrollment.reference_doctype, enrollment.reference_name):
		enrollment.status = "Exited"
		enrollment.save(ignore_permissions=True)
		return
	ref_doc = frappe.get_doc(enrollment.reference_doctype, enrollment.reference_name)
	state = get_state(enrollment)

	if enrollment.status == "Waiting":
		waiting_for = state.get("waiting_for") or {}
		if wait_result is None:
			# scheduler path: only due timeouts resume
			if not enrollment.wait_until or get_datetime(enrollment.wait_until) > now_datetime():
				return
			wait_result = "timeout" if waiting_for.get("kind") in ("reply", "link_clicked") else "done"
		state["wait_result"] = wait_result
		state.pop("waiting_for", None)
		enrollment.status = "Active"
		enrollment.wait_until = None
		if waiting_for.get("kind") != "window":
			enrollment.current_step += 1  # move past the satisfied wait/goal op

	frappe.flags.in_crm_automation = True
	try:
		ops_run = 0
		while enrollment.status == "Active":
			ops_run += 1
			if ops_run > MAX_OPS_PER_ADVANCE:
				log_step(
					enrollment,
					enrollment.current_step,
					"loop_guard",
					"Failed",
					_("Too many steps — possible go_to loop"),
				)
				enrollment.status = "Failed"
				break
			if enrollment.current_step >= len(program):
				enrollment.status = "Completed"
				break
			op = program[enrollment.current_step]
			kind = op.get("op")

			if kind == "end":
				enrollment.status = "Completed"
				break
			if kind == "jump":
				enrollment.current_step = op["to"]
				continue
			if kind == "exit":
				log_step(enrollment, enrollment.current_step, "exit", "Success", _("Removed from automation"))
				enrollment.status = "Exited"
				break
			if kind == "stop_if":
				if evaluate_condition_groups(op.get("groups"), ref_doc):
					log_step(
						enrollment, enrollment.current_step, "stop_if", "Success", _("Stop condition met")
					)
					enrollment.status = "Exited"
					break
				enrollment.current_step += 1
				continue
			if kind == "branch":
				if evaluate_condition_groups(op.get("groups"), ref_doc, state):
					enrollment.current_step += 1
				else:
					enrollment.current_step = op["else_to"]
				continue
			if kind == "split":
				enrollment.current_step = resolve_split(op, enrollment, state)
				continue
			if kind == "goal":
				outcome = (op.get("step") or {}).get("outcome") or "continue"
				if state.pop("goal_met", None):
					log_step(enrollment, enrollment.current_step, "goal", "Success", _("Goal met"))
					enrollment.current_step += 1
					continue
				if outcome == "end":
					log_step(
						enrollment, enrollment.current_step, "goal", "Skipped", _("Goal not met — ended")
					)
					enrollment.status = "Exited"
					break
				if outcome == "wait":
					state["waiting_for"] = {"kind": "goal"}
					enrollment.status = "Waiting"
					enrollment.wait_until = None
					break
				enrollment.current_step += 1
				continue
			if kind == "wait":
				if not begin_wait(op.get("step") or {}, enrollment, state):
					break  # now Waiting
				continue  # zero-length wait: proceed

			# --- action op ---
			step = op.get("step") or {}
			step_type = step.get("type")

			gate = op.get("gate")
			if gate and not evaluate_condition_groups(gate, ref_doc, state):
				log_step(enrollment, enrollment.current_step, step_type, "Skipped", _("Condition not met"))
				enrollment.current_step += 1
				continue

			if step_type in COMMUNICATION_TYPES and not within_time_window(automation):
				state["waiting_for"] = {"kind": "window"}
				enrollment.status = "Waiting"
				enrollment.wait_until = to_naive_utc_free(next_window_open(automation))
				break

			try:
				detail = execute_step(step, ref_doc, enrollment)
				log_step(enrollment, enrollment.current_step, step_type, "Success", detail)
			except Exception:
				frappe.log_error(frappe.get_traceback(), f"CRM Automation: step failed ({automation.name})")
				log_step(enrollment, enrollment.current_step, step_type, "Failed", _("See error log"))
			enrollment.current_step += 1
			ref_doc.reload()
	finally:
		frappe.flags.in_crm_automation = False

	set_state(enrollment, state)
	enrollment.save(ignore_permissions=True)


def resolve_split(op, enrollment, state) -> int:
	"""Random weighted path, sticky per enrollment (GHL semantics)."""
	sticky = state.setdefault("splits", {})
	key = str(enrollment.current_step)
	if key in sticky:
		return int(sticky[key])
	paths = op.get("paths") or []
	total = sum(p["percent"] for p in paths) or 1
	pick = random.uniform(0, total)
	cumulative = 0.0
	target = paths[-1]["to"] if paths else enrollment.current_step + 1
	for path in paths:
		cumulative += path["percent"]
		if pick <= cumulative:
			target = path["to"]
			break
	sticky[key] = target
	return target


def begin_wait(step: dict, enrollment, state: dict) -> bool:
	"""Set up a wait; returns True when there is nothing to wait for."""
	mode = step.get("mode") or "duration"
	now = now_datetime()

	if mode == "duration":
		until = add_to_date(
			now,
			days=int(step.get("days") or 0),
			hours=int(step.get("hours") or 0),
			minutes=int(step.get("minutes") or 0),
		)
		if until <= now:
			enrollment.current_step += 1
			return True
		state["waiting_for"] = {"kind": "duration"}
		enrollment.wait_until = until

	elif mode == "until_time":
		until = next_occurrence(step.get("time") or "09:00", step.get("weekdays"))
		state["waiting_for"] = {"kind": "duration"}
		enrollment.wait_until = until

	elif mode == "until_reply":
		state["waiting_for"] = {"kind": "reply"}
		enrollment.wait_until = (
			add_to_date(now, hours=int(step["timeout_hours"])) if step.get("timeout_hours") else None
		)

	elif mode == "until_link_click":
		state["waiting_for"] = {"kind": "link_clicked", "link": step.get("link")}
		enrollment.wait_until = (
			add_to_date(now, hours=int(step["timeout_hours"])) if step.get("timeout_hours") else None
		)

	enrollment.status = "Waiting"
	return False


def next_occurrence(time_str: str, weekdays: list | None):
	"""Next datetime at HH:MM, optionally restricted to given weekday names."""
	now = now_datetime()
	hour, minute = (int(x) for x in time_str.split(":")[:2])
	candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
	for _i in range(8):
		if candidate > now and (not weekdays or candidate.strftime("%A") in weekdays):
			return candidate
		candidate = add_to_date(candidate, days=1)
	return candidate


def handle_event_for_waiters(kind: str, ref_doctype: str, ref_name: str, payload: dict) -> None:
	"""Resume enrollments waiting for this event (wait until reply / link click)."""
	for name in _active_enrollments(ref_doctype, ref_name, status="Waiting"):
		enr = frappe.get_doc("CRM Automation Enrollment", name)
		waiting_for = get_state(enr).get("waiting_for") or {}
		if waiting_for.get("kind") != kind:
			continue
		if kind == "link_clicked" and waiting_for.get("link") and waiting_for["link"] != payload.get("link"):
			continue
		advance_enrollment(name, wait_result="event")


def handle_goal_event(goal_event: str, ref_doctype: str, ref_name: str, payload: dict) -> None:
	"""GHL Goal Event: pull enrolled contacts forward to a matching goal step."""
	for name in _active_enrollments(ref_doctype, ref_name):
		enr = frappe.get_doc("CRM Automation Enrollment", name)
		automation = frappe.get_doc("CRM Automation", enr.automation)
		program = parse_json(automation.compiled_steps) or []
		for index in range(len(program)):
			op = program[index]
			if op.get("op") != "goal":
				continue
			goal = op.get("step") or {}
			if goal.get("event") != goal_event:
				continue
			value = goal.get("value")
			if value and str(value) not in (
				str(payload.get("value") or ""),
				str(payload.get("link") or ""),
				str(payload.get("tag") or ""),
			):
				continue
			if index < enr.current_step:
				continue  # goal already behind
			state = get_state(enr)
			state["goal_met"] = True
			state.pop("waiting_for", None)
			set_state(enr, state)
			enr.current_step = index
			enr.status = "Active"
			enr.wait_until = None
			log_step(enr, index, "goal", "Success", _("Goal event: {0}").format(goal_event))
			enr.save(ignore_permissions=True)
			advance_enrollment(enr.name)
			break


def _active_enrollments(ref_doctype: str, ref_name: str, status=None) -> list[str]:
	filters = {
		"reference_doctype": ref_doctype,
		"reference_name": ref_name,
		"status": status or ["in", ["Active", "Waiting"]],
	}
	return frappe.get_all("CRM Automation Enrollment", filters=filters, pluck="name")


def process_due_enrollments() -> None:
	"""Scheduler tick: resume enrollments whose wait/timeout has elapsed."""
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
	process_date_reminders_tick()


# ---------------------------------------------------------------------------
# time window (GHL workflow settings → Time Window)
# ---------------------------------------------------------------------------


def within_time_window(automation) -> bool:
	if not automation.get("time_window_enabled"):
		return True
	now = now_datetime()
	days = parse_json(automation.get("window_days")) or []
	if days and now.strftime("%A") not in days:
		return False
	start = str(automation.get("window_start") or "00:00:00")[:5]
	end = str(automation.get("window_end") or "23:59:59")[:5]
	current = now.strftime("%H:%M")
	return start <= current <= end


def next_window_open(automation):
	start = str(automation.get("window_start") or "09:00:00")[:5]
	days = parse_json(automation.get("window_days")) or None
	return next_occurrence(start, days)


def to_naive_utc_free(value):
	return value  # naive system-tz datetime, as the rest of the runtime uses


# ---------------------------------------------------------------------------
# actions
# ---------------------------------------------------------------------------


def execute_step(step: dict, ref_doc, enrollment=None) -> str:
	step_type = step.get("type")
	handler = {
		"send_email": step_send_email,
		"send_sms": step_send_sms,
		"send_whatsapp_template": step_send_whatsapp_template,
		"create_task": step_create_task,
		"assign": step_assign,
		"add_note": step_add_note,
		"add_tag_comment": step_add_note,
		"add_tag": step_add_tag,
		"remove_tag": step_remove_tag,
		"set_field": step_set_field,
		"notify": step_notify,
		"convert_to_deal": step_convert_to_deal,
		"webhook": step_webhook,
		"add_to_workflow": step_add_to_workflow,
		"remove_from_workflow": step_remove_from_workflow,
	}.get(step_type)
	if not handler:
		frappe.throw(_("Unknown step type: {0}").format(step_type))
	return handler(step, ref_doc)


def render(text: str, ref_doc) -> str:
	if not text:
		return ""

	def tracked_link(slug: str) -> str:
		from crm.api.links import personal_link_url

		return personal_link_url(slug, ref_doc.doctype, ref_doc.name)

	context = ref_doc.as_dict()
	context["tracked_link"] = tracked_link
	return frappe.render_template(text, context)


def step_send_email(step, ref_doc) -> str:
	recipient = ref_doc.get("email")
	if not recipient:
		return _("Skipped: record has no email")
	subject = step.get("subject") or ""
	message = step.get("message") or ""
	if step.get("email_template") and frappe.db.exists("Email Template", step["email_template"]):
		template = frappe.get_doc("Email Template", step["email_template"])
		subject = subject or template.subject
		message = message or (template.response_html or template.response)
	frappe.sendmail(
		recipients=[recipient],
		subject=render(subject or _("Message from {0}").format(frappe.local.site), ref_doc),
		message=render(message, ref_doc),
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
	from frappe.desk.form import assign_to

	users = step.get("users") or ([step["user"]] if step.get("user") else [])
	users = [u for u in users if u and frappe.db.exists("User", u)]
	if not users:
		return _("Skipped: no valid user to assign")

	if step.get("only_if_unassigned"):
		from crm.api.doc import get_assigned_users

		if get_assigned_users(ref_doc.doctype, ref_doc.name):
			return _("Skipped: already assigned")

	user = users[0]
	if len(users) > 1:  # equal round robin: least open assignments among the pool
		counts = {u: 0 for u in users}
		rows = frappe.get_all(
			"ToDo",
			filters={"allocated_to": ["in", users], "status": "Open"},
			fields=["allocated_to", "count(name) as total"],
			group_by="allocated_to",
		)
		for row in rows:
			counts[row.allocated_to] = row.total
		user = min(users, key=lambda u: counts[u])

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


def step_add_note(step, ref_doc) -> str:
	ref_doc.add_comment("Comment", render(step.get("comment") or step.get("note") or "", ref_doc))
	return _("Note added")


def step_add_tag(step, ref_doc) -> str:
	tag = (step.get("tag") or "").strip()
	if not tag:
		return _("Skipped: no tag")
	from frappe.desk.doctype.tag.tag import add_tag

	add_tag(tag, ref_doc.doctype, ref_doc.name)
	return _("Tag {0} added").format(tag)


def step_remove_tag(step, ref_doc) -> str:
	tag = (step.get("tag") or "").strip()
	if not tag:
		return _("Skipped: no tag")
	from frappe.desk.doctype.tag.tag import remove_tag

	remove_tag(tag, ref_doc.doctype, ref_doc.name)
	return _("Tag {0} removed").format(tag)


def step_set_field(step, ref_doc) -> str:
	field = step.get("field")
	if not field or not ref_doc.meta.get_field(field):
		frappe.throw(_("Invalid field: {0}").format(field))
	ref_doc.set(field, step.get("value"))
	ref_doc.save(ignore_permissions=True)
	return _("{0} set to {1}").format(field, step.get("value"))


def step_convert_to_deal(step, ref_doc) -> str:
	if ref_doc.doctype != "CRM Lead":
		return _("Skipped: only leads can be converted")
	if ref_doc.get("converted"):
		return _("Skipped: lead already converted")
	from crm.fcrm.doctype.crm_lead.crm_lead import convert_to_deal

	ref_doc.flags.ignore_permissions = True
	deal = convert_to_deal(lead=ref_doc.name, doc=ref_doc)
	return _("Converted to deal {0}").format(deal)


def step_webhook(step, ref_doc) -> str:
	import requests

	url = step.get("url") or ""
	if not url.startswith(("http://", "https://")):
		frappe.throw(_("Webhook URL must start with http(s)://"))
	method = (step.get("method") or "POST").upper()
	headers = step.get("headers") or {}
	if step.get("body"):
		body = render(step.get("body"), ref_doc)
		try:
			payload = json.loads(body)
		except ValueError:
			payload = {"body": body}
	else:
		payload = {
			"doctype": ref_doc.doctype,
			"name": ref_doc.name,
			"data": {
				k: v
				for k, v in ref_doc.as_dict().items()
				if isinstance(v, (str, int, float, bool)) or v is None
			},
		}
	response = requests.request(method, url, json=payload, headers=headers, timeout=15)
	return _("Webhook {0} → {1}").format(url, response.status_code)


def step_add_to_workflow(step, ref_doc) -> str:
	target = step.get("automation")
	if not target or not frappe.db.exists("CRM Automation", target):
		return _("Skipped: automation not found")
	frappe.flags.in_crm_automation = False
	try:
		result = enroll(target, ref_doc.doctype, ref_doc.name)
	finally:
		frappe.flags.in_crm_automation = True
	return _("Enrolled in {0}").format(target) if result else _("Skipped: not enrolled (filters/re-entry)")


def step_remove_from_workflow(step, ref_doc) -> str:
	target = step.get("automation")
	filters = {
		"reference_doctype": ref_doc.doctype,
		"reference_name": ref_doc.name,
		"status": ["in", ["Active", "Waiting"]],
	}
	if target and target != "all":
		filters["automation"] = target
	count = 0
	for name in frappe.get_all("CRM Automation Enrollment", filters=filters, pluck="name"):
		enr = frappe.get_doc("CRM Automation Enrollment", name)
		enr.status = "Exited"
		enr.wait_until = None
		enr.save(ignore_permissions=True)
		count += 1
	return _("Removed from {0} automation(s)").format(count)


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


# ---------------------------------------------------------------------------
# conditions
# ---------------------------------------------------------------------------


def condition_groups_of(container: dict) -> list | None:
	"""Normalize: condition_groups (list of AND-groups, OR between) or single condition."""
	groups = container.get("condition_groups")
	if groups:
		return groups
	condition = container.get("condition") or container.get("trigger_condition")
	if condition:
		if isinstance(condition, str):
			condition = parse_json(condition)
		if condition and condition.get("field"):
			return [[condition]]
	return None


def evaluate_condition_groups(groups, ref_doc, state: dict | None = None) -> bool:
	if not groups:
		return True
	for group in groups:
		if all(evaluate_condition(c, ref_doc, state) for c in group):
			return True
	return False


def evaluate_condition(condition: dict, ref_doc, state: dict | None = None) -> bool:
	field = condition.get("field")
	operator = condition.get("operator") or "equals"
	expected = condition.get("value")

	if field == "wait_result" and state is not None:
		actual = state.get("wait_result")
	else:
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
	if operator == "greater_than":
		try:
			return float(actual) > float(expected)
		except (TypeError, ValueError):
			return False
	if operator == "less_than":
		try:
			return float(actual) < float(expected)
		except (TypeError, ValueError):
			return False
	return False


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------


def validate_steps(steps, _top=True) -> None:
	if not isinstance(steps, list) or (_top and not steps):
		frappe.throw(_("Steps must be a non-empty list"))
	for i, step in enumerate(steps):
		if not isinstance(step, dict) or step.get("type") not in STEP_TYPES:
			frappe.throw(_("Step {0}: unknown type {1}").format(i + 1, (step or {}).get("type")))
		step_type = step["type"]
		if step_type == "wait":
			mode = step.get("mode") or "duration"
			if mode not in WAIT_MODES:
				frappe.throw(_("Step {0}: unknown wait mode {1}").format(i + 1, mode))
			if mode == "duration":
				total = (
					int(step.get("days") or 0) * 1440
					+ int(step.get("hours") or 0) * 60
					+ int(step.get("minutes") or 0)
				)
				if total <= 0:
					frappe.throw(_("Step {0}: wait must have a positive duration").format(i + 1))
		if step_type == "stop_if" and not condition_groups_of(step):
			frappe.throw(_("Step {0}: stop_if requires a condition").format(i + 1))
		if step_type == "goal" and step.get("event") not in GOAL_EVENTS:
			frappe.throw(_("Step {0}: unknown goal event").format(i + 1))
		if step_type == "if_else":
			branches = step.get("branches") or []
			if not branches:
				frappe.throw(_("Step {0}: if_else requires at least one branch").format(i + 1))
			for branch in branches:
				validate_steps(branch.get("steps") or [], _top=False)
			validate_steps(step.get("else_steps") or [], _top=False)
		if step_type == "split":
			paths = step.get("paths") or []
			total = sum(float(p.get("percent") or 0) for p in paths)
			if not paths or abs(total - 100) > 0.01:
				frappe.throw(_("Step {0}: split percentages must total 100").format(i + 1))
			for path in paths:
				validate_steps(path.get("steps") or [], _top=False)
		for cond_key in ("condition",):
			cond = step.get(cond_key)
			if cond and (cond.get("operator") or "equals") not in CONDITION_OPERATORS:
				frappe.throw(_("Step {0}: unknown condition operator").format(i + 1))
	if _top:
		compile_steps(steps)  # surfaces unresolved go_to targets


def parse_json(value):
	if not value:
		return None
	if isinstance(value, (list, dict)):
		return value
	try:
		return json.loads(value)
	except (ValueError, TypeError):
		return None


def log_step(enrollment, step_index: int, action: str, status: str, detail: str = "") -> None:
	enrollment.append(
		"logs",
		{"step_index": step_index, "action": action or "", "status": status, "detail": (detail or "")[:500]},
	)


# ---------------------------------------------------------------------------
# date reminders (birthday / custom date trigger)
# ---------------------------------------------------------------------------


def process_date_reminders_tick() -> None:
	"""Hourly-ish: enroll records whose configured date field matches today+offset.

	trigger_config: {"date_field": "...", "offset_days": N, "direction": "before"|"after",
	                 "doctype": "CRM Lead"|"CRM Deal", "annual": true|false}
	"""
	cache_key = f"crm_date_reminders_ran|{frappe.utils.today()}"
	if frappe.cache.get_value(cache_key):
		return
	frappe.cache.set_value(cache_key, 1, expires_in_sec=60 * 60 * 20)

	automations = frappe.get_all(
		"CRM Automation", filters={"enabled": 1, "trigger_event": "Date Reminder"}, pluck="name"
	)
	for name in automations:
		try:
			automation = frappe.get_doc("CRM Automation", name)
			config = parse_json(automation.trigger_config) or {}
			field = config.get("date_field")
			doctype = config.get("doctype") or "CRM Lead"
			if not field or doctype not in ("CRM Lead", "CRM Deal"):
				continue
			meta_field = frappe.get_meta(doctype).get_field(field)
			if not meta_field or meta_field.fieldtype not in ("Date", "Datetime"):
				continue
			offset = int(config.get("offset_days") or 0)
			if (config.get("direction") or "before") == "before":
				target = frappe.utils.add_days(frappe.utils.today(), offset)
			else:
				target = frappe.utils.add_days(frappe.utils.today(), -offset)

			if config.get("annual"):
				month_day = target[5:]
				rows = frappe.get_all(
					doctype, filters={field: ["like", f"%-{month_day}%"]}, pluck="name", limit=500
				)
			else:
				rows = frappe.get_all(
					doctype,
					filters={field: ["between", [f"{target} 00:00:00", f"{target} 23:59:59"]]}
					if meta_field.fieldtype == "Datetime"
					else {field: target},
					pluck="name",
					limit=500,
				)
			for row in rows:
				enroll(name, doctype, row, {"date_field": field})
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"CRM Automation: date reminder failed ({name})")


# ---------------------------------------------------------------------------
# doc_events glue
# ---------------------------------------------------------------------------


def _status_actually_changed(doc) -> bool:
	# get_doc_before_save is absent on insert, so this stays False for new docs
	# (has_value_changed would report True there)
	previous = doc.get_doc_before_save()
	return bool(previous) and previous.get("status") != doc.get("status")


def on_lead_created(doc, method=None):
	process_event("lead_created", doc)


def on_lead_updated(doc, method=None):
	if _status_actually_changed(doc):
		process_event("lead_status_changed", doc, {"status": doc.status})


def on_deal_created(doc, method=None):
	process_event("deal_created", doc)


def on_deal_updated(doc, method=None):
	if _status_actually_changed(doc):
		process_event("deal_status_changed", doc, {"status": doc.status})


def on_whatsapp_received(doc, method=None):
	if doc.get("type") == "Incoming":
		process_event("whatsapp_received", doc, {"channel": "whatsapp"})


def on_booking_created(doc, method=None):
	process_event("booking_created", doc)


def on_booking_updated(doc, method=None):
	if not _status_actually_changed(doc):
		return
	event = {
		"Cancelled": "booking_cancelled",
		"No Show": "booking_no_show",
		"Completed": "booking_completed",
	}.get(doc.status)
	if event:
		process_event(event, doc, {"status": doc.status})


def on_communication_update(doc, method=None):
	"""Email opened (read tracking) and email replies from the shared inbox."""
	try:
		if doc.get("communication_medium") != "Email":
			return
		previous = doc.get_doc_before_save()
		if (
			previous
			and not previous.get("read_by_recipient")
			and doc.get("read_by_recipient")
			and doc.get("sent_or_received") == "Sent"
		):
			process_event("email_opened", doc, {"channel": "email"})
	except Exception:
		frappe.log_error(frappe.get_traceback(), "CRM Automation: communication event failed")


def on_communication_insert(doc, method=None):
	if doc.get("communication_medium") == "Email" and doc.get("sent_or_received") == "Received":
		process_event("email_replied", doc, {"channel": "email"})


def on_tag_added(doc, method=None):
	if doc.get("document_type") in ("CRM Lead", "CRM Deal"):
		ref = frappe.get_doc(doc.document_type, doc.document_name)
		process_event("tag_added", ref, {"tag": doc.tag})


def on_tag_removed(doc, method=None):
	if doc.get("document_type") in ("CRM Lead", "CRM Deal"):
		if frappe.db.exists(doc.document_type, doc.document_name):
			ref = frappe.get_doc(doc.document_type, doc.document_name)
			process_event("tag_removed", ref, {"tag": doc.tag})


def on_task_updated(doc, method=None):
	if _status_actually_changed(doc) and doc.status == "Done":
		process_event("task_completed", doc, {"title": doc.title})


def on_note_created(doc, method=None):
	process_event("note_added", doc)
