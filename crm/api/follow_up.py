"""Follow-up reminders for CRM Lead and CRM Deal.

A rep records the next touch on the record itself via the ``next_follow_up``
Datetime field. This module is the part that makes that field act: a scheduler
job picks up records whose follow up is due (optionally a configurable lead time
early) and notifies whoever is on the hook for it.

Delivery is an in-app ``CRM Notification`` -- the same channel used for mentions,
assignments and task notifications -- plus an optional email, both configured in
FCRM Settings under "Follow Up Reminders".

Bookkeeping is a single ``follow_up_reminder_sent`` checkbox on the record rather
than a queue of pending reminder rows, which keeps the three lifecycle rules the
feature needs almost free:

* rescheduled -- ``next_follow_up`` changed, so :func:`reset_follow_up_reminder`
  clears the flag on save and the new time gets its own reminder;
* cleared -- no ``next_follow_up``, so the record never matches the query;
* closed -- won/lost (or a converted lead) is filtered out, so a dead deal never
  fires a reminder that is still technically due.
"""

import frappe
from frappe import _
from frappe.utils import add_to_date, get_datetime, now_datetime

from crm.fcrm.doctype.crm_notification.crm_notification import notify_user

FOLLOW_UP_DOCTYPES = ("CRM Lead", "CRM Deal")

# Statuses that mean "there is nothing left to follow up on".
CLOSED_STATUS_TYPES = ("Won", "Lost")

# Cap per scheduler tick so a large backlog (a bulk import of back-dated follow
# ups, or a scheduler that was down for a while) can't monopolise the worker.
# The remainder is picked up on the next tick, oldest first.
BATCH_SIZE = 200

VALID_INTERVALS = ("minutes", "hours", "days")


def trigger_follow_up_reminders():
	"""Scheduler entry point: notify assignees about follow ups that are now due."""
	if frappe.flags.in_import or frappe.flags.in_patch or frappe.flags.in_install:
		return

	settings = frappe.get_cached_doc("FCRM Settings")
	if not settings.get("enable_follow_up_reminders"):
		return

	# Reminders fire `before` ahead of the follow up time, so anything due up to
	# that far in the future is already actionable.
	cutoff = add_to_date(now_datetime(), **get_lead_time(settings))
	send_email = bool(settings.get("send_follow_up_reminder_email"))

	# No explicit commit: the whole run is one transaction, so a failure that
	# escapes the per-record handler rolls back the sent flags *and* the
	# notifications they were paired with. The next tick then re-sends cleanly
	# instead of leaving records marked as reminded but never notified.
	for doctype in FOLLOW_UP_DOCTYPES:
		for record in get_due_records(doctype, cutoff):
			# send_reminder isolates each recipient, so what reaches here is a
			# failure to work out *who* to notify at all -- nothing was sent, and
			# the flag stays clear so the next tick tries the record again.
			if run_in_savepoint(
				lambda record=record: send_reminder(doctype, record, send_email=send_email),
				title=f"Follow up reminder failed for {doctype} {record.name}",
			):
				frappe.db.set_value(doctype, record.name, "follow_up_reminder_sent", 1, update_modified=False)


def get_lead_time(settings):
	"""Return ``add_to_date`` kwargs for how far ahead of the follow up to remind."""
	before = frappe.utils.cint(settings.get("follow_up_reminder_before"))
	interval = settings.get("follow_up_reminder_interval") or "minutes"

	if before <= 0:
		return {"minutes": 0}
	if interval not in VALID_INTERVALS:
		interval = "minutes"

	return {interval: before}


def get_due_records(doctype, cutoff):
	"""Records with a follow up due by ``cutoff`` that haven't been reminded yet."""
	owner_field = get_owner_field(doctype)

	# `is set` is load-bearing, not belt-and-braces: the query builder compiles a
	# `<=` on a Datetime to `IFNULL(next_follow_up, '0001-01-01') <= cutoff`, so
	# without it every record that has *no* follow up date matches and the first
	# scheduler tick reminds every lead and deal in the system. Filters are a list
	# rather than a dict because both conditions are on the same fieldname.
	filters = [
		["next_follow_up", "is", "set"],
		["next_follow_up", "<=", cutoff],
		["follow_up_reminder_sent", "=", 0],
	]

	closed_statuses = frappe.get_all(
		f"{doctype} Status", filters={"type": ("in", CLOSED_STATUS_TYPES)}, pluck="name"
	)
	if closed_statuses:
		filters.append(["status", "not in", closed_statuses])

	if doctype == "CRM Lead":
		# A converted lead lives on as a deal; the deal carries the follow up.
		filters.append(["converted", "=", 0])

	return frappe.get_all(
		doctype,
		filters=filters,
		fields=["name", "next_follow_up", "owner", "_assign", owner_field, *get_title_fields(doctype)],
		order_by="next_follow_up asc",
		limit=BATCH_SIZE,
	)


def send_reminder(doctype, record, send_email=False):
	"""Notify everyone responsible for ``record`` that its follow up is due.

	The record is marked reminded once, so every recipient gets their own
	savepoint: one user whose notification blows up must not swallow the
	reminder for the others, and must not poison the surrounding transaction.
	Whoever failed is left in the Error Log rather than retried forever.
	"""
	recipients = get_recipients(doctype, record)
	if not recipients:
		return

	title = get_record_title(doctype, record)
	follow_up_on = get_datetime(record.next_follow_up)

	notified = []
	for user in recipients:
		if run_in_savepoint(
			lambda user=user: notify_user(
				{
					# No from_user: this is the system reminding you, not a
					# colleague. It also keeps notify_user's "don't notify
					# yourself" guard from swallowing the reminder, which is
					# almost always self-directed.
					"owner": None,
					"assigned_to": user,
					"notification_type": "Follow Up",
					"message": _("Follow up on {0} {1} is due").format(doctype, record.name),
					"notification_text": get_notification_text(doctype, title, follow_up_on),
					"reference_doctype": doctype,
					"reference_docname": record.name,
					"redirect_to_doctype": doctype,
					"redirect_to_docname": record.name,
				}
			),
			title=f"Follow up reminder failed for {doctype} {record.name} ({user})",
		):
			notified.append(user)

	# Email only the people whose in-app reminder actually landed, and never let
	# a mail failure cost them that reminder -- sendmail only queues, so a raise
	# here means the queue row itself failed.
	if send_email and notified:
		run_in_savepoint(
			lambda: send_reminder_email(doctype, record, notified, title, follow_up_on),
			title=f"Follow up reminder email failed for {doctype} {record.name}",
		)


def run_in_savepoint(fn, title):
	"""Run ``fn``, returning whether it succeeded and undoing its writes if not.

	The savepoint matters as much as the ``try``: without it a failed statement
	leaves the surrounding transaction dirty, so the caller's later writes (the
	``follow_up_reminder_sent`` flag, the next recipient's notification) would go
	down with it. ``frappe.database.database.savepoint`` can't be used here
	because it swallows the exception, and the caller needs to know.
	"""
	# Unique per call: these nest (a per-recipient savepoint inside the
	# per-record one) and re-using a name would make MySQL drop the outer
	# savepoint, so releasing it afterwards fails.
	sp = f"crm_follow_up_{frappe.generate_hash(length=8)}"
	frappe.db.savepoint(sp)
	try:
		fn()
	except Exception:
		frappe.db.rollback(save_point=sp)
		frappe.log_error(title=title)
		return False

	frappe.db.release_savepoint(sp)
	return True


def get_recipients(doctype, record):
	"""Assigned users, falling back to the record owner so a reminder is never lost."""
	users = frappe.parse_json(record.get("_assign") or "[]") or []

	if not users:
		# Nobody assigned -- the issue asks that we fall back rather than send
		# nothing. Lead/deal owner first, then whoever created the record.
		users = [record.get(get_owner_field(doctype)) or record.get("owner")]

	seen = {}
	for user in users:
		if user and user not in seen and frappe.db.get_value("User", user, "enabled"):
			seen[user] = True

	return list(seen)


def get_owner_field(doctype):
	return "lead_owner" if doctype == "CRM Lead" else "deal_owner"


def get_title_fields(doctype):
	return ["lead_name"] if doctype == "CRM Lead" else ["organization", "lead_name"]


def get_record_title(doctype, record):
	if doctype == "CRM Lead":
		return record.get("lead_name") or record.name
	return record.get("organization") or record.get("lead_name") or record.name


def get_notification_text(doctype, title, follow_up_on):
	label = _("lead") if doctype == "CRM Lead" else _("deal")
	formatted = frappe.utils.format_datetime(follow_up_on)

	return f"""
		<div class="mb-2 leading-5 text-ink-gray-5">
			<span>{
		_("Follow up on {0} {1} is due on {2}").format(
			label,
			f'<span class="font-medium text-ink-gray-9">{ frappe.utils.escape_html(title) }</span>',
			f'<span class="font-medium text-ink-gray-9">{ formatted }</span>',
		)
	}</span>
		</div>
	"""


def send_reminder_email(doctype, record, recipients, title, follow_up_on):
	label = _("Lead") if doctype == "CRM Lead" else _("Deal")
	link = frappe.utils.get_url(f"/crm/{'leads' if doctype == 'CRM Lead' else 'deals'}/{record.name}")
	safe_title = frappe.utils.escape_html(title)

	message = f"""
		<div style="font-family: Arial, sans-serif; max-width: 600px;">
			<h2 style="color: #333;">{_("Follow Up Reminder")}</h2>
			<p>{_("A follow up you are responsible for is due:")}</p>
			<div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0;">
				<h3 style="margin: 0; color: #007bff;">{safe_title}</h3>
				<p style="margin: 5px 0;"><strong>{label}:</strong> {record.name}</p>
				<p style="margin: 5px 0;"><strong>{_("Follow up on")}:</strong> {frappe.utils.format_datetime(follow_up_on)}</p>
			</div>
			<p><a href="{link}">{_("Open in CRM")}</a></p>
		</div>
	"""

	frappe.sendmail(
		recipients=recipients,
		subject=_("Follow up due: {0}").format(title),
		message=message,
		reference_doctype=doctype,
		reference_name=record.name,
	)


def reset_follow_up_reminder(doc):
	"""Clear the sent flag whenever the follow up is rescheduled or cleared.

	Called from CRM Lead / CRM Deal ``validate`` so the new time gets its own
	reminder instead of inheriting the previous one's "already sent" state.
	"""
	if doc.has_value_changed("next_follow_up"):
		doc.follow_up_reminder_sent = 0
