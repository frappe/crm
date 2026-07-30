"""Support-journey automation (E7).

Composes EXISTING CRM primitives — CRM Task, ToDo assignment (`frappe...assign_to.add`),
CRM Notification, SLA — into two journeys:

  1. Onboarding journey  — a Deal entering a *Won* status seeds staged onboarding tasks,
     assigns them to the deal owner, and notifies them.
  2. Missed-call recovery — a missed/no-answer inbound Avaya call log seeds a callback
     task for the receiving agent (or a fallback owner) + notifies them.

Design (per project rules):
- These are EXPLICIT, named doc_event handlers registered in hooks.py — NOT anonymous
  `on_update` side-effects buried in a controller. Each handler detects its own trigger
  (a real entry into Won, a *missed* call) and is idempotent.
- The actual work (creating Tasks/Notifications with `ignore_permissions`) runs in a
  BACKGROUND JOB via `frappe.enqueue`, not inline on the user's save: this keeps
  `ignore_permissions` on a legitimate (non-request) path and adds no latency to the
  Deal/Call-Log write.
"""
import frappe
from frappe.utils import add_days, cstr, nowdate

# --- Onboarding journey -----------------------------------------------------------

# Staged onboarding tasks seeded when a Deal is Won. (title, days_from_now, priority)
ONBOARDING_TASKS = (
	("Welcome call with new customer", 1, "High"),
	("Send onboarding pack & credentials", 2, "Medium"),
	("Schedule kickoff / implementation session", 5, "Medium"),
	("Day-30 check-in", 30, "Low"),
)

# A marker task title used to detect "already onboarded" (idempotency).
_ONBOARDING_MARKER = ONBOARDING_TASKS[0][0]


def on_deal_update(doc, method=None):
	"""CRM Deal doc_event (on_update + after_insert). Fire the onboarding journey ONCE,
	on the Deal *entering* a Won status — whether by transition or by being created
	directly as Won (data import / quick-create). Idempotency is enforced downstream by
	the marker-task check, so double-registration is safe."""
	if not _entered_won(doc):
		return
	# Detection is cheap + inline; the work runs in the background (legit ignore_permissions
	# path, no save-latency). Pass the triggering user so the notification's from_user is
	# distinct from the assignee.
	frappe.enqueue(
		"crm.automation.support_journey.run_onboarding_journey",
		queue="short",
		enqueue_after_commit=True,
		deal_name=doc.name,
		triggered_by=frappe.session.user,
	)


def _entered_won(doc) -> bool:
	"""True when this save results in the deal being Won for the first time.

	Covers two cases:
	  - transition: an existing deal whose status changed from non-Won to Won;
	  - create-as-won: a brand-new deal saved directly with a Won status.
	Won A -> Won B is NOT a fresh entry (guarded)."""
	if not doc.get("status"):
		return False
	if frappe.db.get_value("CRM Deal Status", doc.status, "type") != "Won":
		return False

	if doc.is_new():
		# Created directly as Won.
		return True
	if not doc.has_value_changed("status"):
		return False
	previous = doc.get_doc_before_save()
	prev_status = previous.status if previous else None
	if not prev_status:
		return True
	# Guard: don't re-run when moving between two Won statuses.
	return frappe.db.get_value("CRM Deal Status", prev_status, "type") != "Won"


def run_onboarding_journey(deal_name: str, triggered_by: str | None = None):
	"""Background job: seed staged onboarding tasks + assign + notify the deal owner.
	Idempotent — a marker-task existence check prevents re-seeding."""
	if not frappe.db.exists("CRM Deal", deal_name):
		return
	deal = frappe.get_doc("CRM Deal", deal_name)
	owner = deal.get("deal_owner") or deal.owner

	if frappe.db.exists(
		"CRM Task",
		{
			"reference_doctype": "CRM Deal",
			"reference_docname": deal.name,
			"title": _ONBOARDING_MARKER,
		},
	):
		return

	created = 0
	for title, offset_days, priority in ONBOARDING_TASKS:
		_create_task(
			title=title,
			doctype="CRM Deal",
			docname=deal.name,
			assigned_to=owner,
			priority=priority,
			due_date=f"{add_days(nowdate(), offset_days)} 17:00:00",
		)
		created += 1

	if owner:
		# from_user must differ from assignee or notify_user() early-returns; fall back
		# to the triggering user, then Administrator.
		from_user = triggered_by if (triggered_by and triggered_by != owner) else "Administrator"
		_notify(
			from_user=from_user,
			assigned_to=owner,
			reference_doctype="CRM Deal",
			reference_docname=deal.name,
			text=f"Deal <b>{cstr(deal.name)}</b> is Won — {created} onboarding tasks created.",
		)
	frappe.db.commit()  # SYSTEM-INTERNAL: background job, persist journey artifacts


# --- Missed-call recovery ---------------------------------------------------------

# CRM Call Log statuses that count as "missed" for recovery (valid status options only).
_MISSED_STATUSES = {"No Answer", "Failed", "Busy"}


def on_call_log_update(doc, method=None):
	"""CRM Call Log doc_event (after_insert + on_update). Seed a callback task for a
	missed *inbound Avaya* call, once (idempotent downstream)."""
	if doc.get("telephony_medium") != "Avaya":
		return
	if doc.get("type") != "Incoming":
		return
	if doc.get("status") not in _MISSED_STATUSES:
		return
	frappe.enqueue(
		"crm.automation.support_journey.run_missed_call_recovery",
		queue="short",
		enqueue_after_commit=True,
		call_log_name=doc.name,
	)


def run_missed_call_recovery(call_log_name: str):
	"""Background job: create a callback task for a missed inbound call. Idempotent."""
	if not frappe.db.exists("CRM Call Log", call_log_name):
		return
	doc = frappe.get_doc("CRM Call Log", call_log_name)
	caller = doc.get("from") or ""
	title = f"Call back missed call from {caller or 'unknown number'}"

	# Assignee: the answering agent is usually null on a missed call — fall back to the
	# call log owner so the callback task actually lands on someone, not an orphan queue.
	agent = doc.get("receiver") or doc.owner

	if frappe.db.exists(
		"CRM Task",
		{
			"reference_doctype": "CRM Call Log",
			"reference_docname": doc.name,
			"title": title,
		},
	):
		return

	_create_task(
		title=title,
		doctype="CRM Call Log",
		docname=doc.name,
		assigned_to=agent,
		priority="High",
		due_date=f"{nowdate()} 17:00:00",
	)

	if agent:
		from_user = doc.owner if doc.owner != agent else "Administrator"
		_notify(
			from_user=from_user,
			assigned_to=agent,
			reference_doctype="CRM Call Log",
			reference_docname=doc.name,
			text=f"Missed Avaya call from <b>{cstr(caller)}</b> — callback task created.",
		)
	frappe.db.commit()  # SYSTEM-INTERNAL: background job, persist journey artifacts


# --- shared helpers ---------------------------------------------------------------


def _create_task(title, doctype, docname, assigned_to, priority, due_date):
	"""Create a CRM Task linked to the reference doc. Runs in a background job, so
	ignore_permissions is on a legitimate (non-request) path."""
	task = frappe.get_doc(
		{
			"doctype": "CRM Task",
			"title": title,
			"status": "Todo",
			"priority": priority,
			"due_date": due_date,
			"assigned_to": assigned_to or None,
			"reference_doctype": doctype,
			"reference_docname": docname,
		}
	)
	task.insert(ignore_permissions=True)  # SYSTEM-INTERNAL: journey automation (bg job)
	return task


def _notify(from_user, assigned_to, reference_doctype, reference_docname, text):
	"""Create a CRM Notification via the existing notify_user helper."""
	from crm.fcrm.doctype.crm_notification.crm_notification import notify_user

	notify_user(
		{
			"owner": from_user,
			"assigned_to": assigned_to,
			"notification_type": "Assignment",
			"message": text,
			"notification_text": text,
			"reference_doctype": reference_doctype,
			"reference_docname": reference_docname,
			"redirect_to_doctype": reference_doctype,
			"redirect_to_docname": reference_docname,
		}
	)
