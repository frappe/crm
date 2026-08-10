# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""CRM domain events published to the automation engine.

Payloads carry identifiers only — never message bodies — because they are snapshotted onto
event subscriptions and run logs.

Correlation: a message event is emitted once per candidate key (thread first, then the
Lead/Deal it belongs to) so both thread-level and record-level waits can match. Emitting
more than once is safe for flows: the outbox deduplicates a pending row per document.
"""

import frappe
from frappe.automation_engine import emit, is_enabled
from frappe.utils import add_to_date, now

CRM_REFERENCE_DOCTYPES = ("CRM Lead", "CRM Deal")
QUALIFIED_STATUS = "Qualified"
OVERDUE_STATUSES = ("Done", "Canceled")

# name -> payload keys, documented for flow authors and the builder.
EVENTS = {
	"crm.prospect_message_sent": (
		"reference_doctype",
		"reference_name",
		"communication",
		"channel",
		"thread",
	),
	"crm.prospect_message_received": (
		"reference_doctype",
		"reference_name",
		"communication",
		"channel",
		"thread",
	),
	"crm.lead_qualified": ("lead", "status"),
	"crm.lead_converted": ("lead", "deal", "contact", "organization"),
	"crm.deal_stage_changed": ("deal", "status", "previous_status"),
	"crm.deal_won": ("deal", "status"),
	"crm.deal_lost": ("deal", "status", "lost_reason"),
	"crm.task_overdue": ("task", "reference_doctype", "reference_name", "due_date"),
}


def on_communication(doc, method=None):
	"""Emit the prospect message event for an email against a Lead or Deal."""
	if not _enabled() or doc.reference_doctype not in CRM_REFERENCE_DOCTYPES:
		return
	if doc.communication_type != "Communication":
		return
	event = "crm.prospect_message_sent" if doc.sent_or_received == "Sent" else "crm.prospect_message_received"
	thread = _email_thread_key(doc)
	payload = _message_payload(doc, doc.name, "Email", thread)
	_emit_correlated(event, doc, payload, [thread, _record_key(doc)])


def on_whatsapp_message(doc, method=None):
	"""Emit the prospect message event for a WhatsApp message against a Lead or Deal."""
	if not _enabled() or doc.reference_doctype not in CRM_REFERENCE_DOCTYPES:
		return
	outgoing = doc.get("type") == "Outgoing"
	event = "crm.prospect_message_sent" if outgoing else "crm.prospect_message_received"
	thread = doc.get("message_id") if outgoing else doc.get("reply_to_message_id")
	payload = _message_payload(doc, doc.name, "WhatsApp", thread)
	_emit_correlated(event, doc, payload, [thread, _record_key(doc)])


def on_lead_update(doc, method=None):
	if not _enabled() or not doc.has_value_changed("status") or doc.status != QUALIFIED_STATUS:
		return
	emit("crm.lead_qualified", doc=doc, payload={"lead": doc.name, "status": doc.status})


def on_deal_update(doc, method=None):
	if not _enabled() or not doc.has_value_changed("status"):
		return
	before = doc.get_doc_before_save()
	payload = {"deal": doc.name, "status": doc.status, "previous_status": before.status if before else None}
	emit("crm.deal_stage_changed", doc=doc, payload=payload, correlation_key=doc.name)
	_emit_deal_outcome(doc, payload)


def emit_lead_converted(lead, deal, contact=None, organization=None):
	if not _enabled():
		return
	payload = {"lead": lead.name, "deal": deal, "contact": contact, "organization": organization}
	emit("crm.lead_converted", doc=lead, payload=payload, correlation_key=lead.name)


def emit_overdue_tasks():
	"""Hourly sweep: emit once for each task that fell due in the last hour."""
	if not _enabled():
		return
	tasks = frappe.get_all(
		"CRM Task",
		filters={
			"status": ("not in", OVERDUE_STATUSES),
			"due_date": ("between", [add_to_date(now(), hours=-1), now()]),
		},
		fields=["name", "reference_doctype", "reference_docname", "due_date"],
	)
	for task in tasks:
		_emit_overdue_task(task)


def _emit_overdue_task(task):
	payload = {
		"task": task.name,
		"reference_doctype": task.reference_doctype,
		"reference_name": task.reference_docname,
		"due_date": str(task.due_date),
	}
	emit(
		"crm.task_overdue",
		doc=frappe.get_doc("CRM Task", task.name),
		payload=payload,
		correlation_key=task.name,
	)


def _emit_deal_outcome(doc, payload):
	status_type = frappe.get_cached_value("CRM Deal Status", doc.status, "type") if doc.status else None
	if status_type == "Won":
		emit("crm.deal_won", doc=doc, payload=payload, correlation_key=doc.name)
	elif status_type == "Lost":
		emit(
			"crm.deal_lost",
			doc=doc,
			payload={**payload, "lost_reason": doc.lost_reason},
			correlation_key=doc.name,
		)


def _emit_correlated(event, doc, payload, keys):
	for key in dict.fromkeys(key for key in keys if key):
		emit(event, doc=doc, payload=payload, correlation_key=key)


def _message_payload(doc, communication, channel, thread) -> dict:
	return {
		"reference_doctype": doc.reference_doctype,
		"reference_name": doc.reference_name,
		"communication": communication,
		"channel": channel,
		"thread": thread,
	}


def _email_thread_key(doc) -> str | None:
	"""Sent mail is keyed by its own Message-ID; a reply by the Message-ID it answers."""
	if doc.sent_or_received == "Sent":
		return _message_key(doc.message_id) or doc.name
	if not doc.in_reply_to:
		return None
	parent = frappe.db.get_value("Communication", doc.in_reply_to, "message_id")
	return _message_key(parent) or doc.in_reply_to


def _message_key(message_id) -> str | None:
	"""Correlation keys are stored in a Data field, which strips the Message-ID's brackets."""
	return message_id.strip("<>").strip() if message_id else None


def _record_key(doc) -> str | None:
	if not (doc.reference_doctype and doc.reference_name):
		return None
	return f"{doc.reference_doctype}:{doc.reference_name}"


def _enabled() -> bool:
	return is_enabled() and not frappe.flags.in_install and not frappe.flags.in_migrate
