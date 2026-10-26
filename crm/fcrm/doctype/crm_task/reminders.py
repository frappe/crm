# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import format_datetime, format_time, now_datetime

from crm.fcrm.doctype.crm_notification.crm_notification import (
	get_record_title,
	highlight,
	notification_html,
	notify_user,
	record_label,
)
from crm.fcrm.doctype.crm_task.rules import TaskDue, follow_up_condition

REMINDER_MINUTES = 15


def send_follow_up_reminders():
	for task in due_soon():
		try:
			remind(task)
			frappe.db.set_value("CRM Task", task.name, "reminded_for", task.due_date, update_modified=False)
		except Exception:
			frappe.log_error(title=f"CRM follow-up reminder failed for task {task.name}")


def due_soon(now=None) -> list:
	now = now or now_datetime()
	task = frappe.qb.DocType("CRM Task")
	return (
		frappe.qb.from_(task)
		.select(
			task.name,
			task.title,
			task.assigned_to,
			task.due_date,
			task.reference_doctype,
			task.reference_docname,
		)
		.where(
			follow_up_condition(task)
			# all-day follow-ups get no reminder; the morning digest lists them
			& (task.all_day == 0)
			& task.assigned_to.isnotnull()
			& (task.due_date > now)
			& (task.due_date <= now + timedelta(minutes=REMINDER_MINUTES))
			& (task.reminded_for.isnull() | (task.reminded_for != task.due_date))
		)
		.run(as_dict=True)
	)


def remind(task):
	due_at = TaskDue(task.assigned_to).user_time(task.due_date).replace(tzinfo=None)
	text = _("Follow-up {0} on {1} {2} is due at {3}").format(
		highlight(task.title),
		record_label(task.reference_doctype),
		highlight(get_record_title(task.reference_doctype, task.reference_docname)),
		highlight(format_time(due_at, "HH:mm")),
	)
	notify_user(
		{
			"assigned_to": task.assigned_to,
			"notification_type": "Reminder",
			# the due date keeps notify_user from dropping the reminder of a rescheduled task as a duplicate
			"message": _("{0}, due {1}").format(task.title, format_datetime(due_at)),
			"notification_text": notification_html(text),
			"reference_doctype": "CRM Task",
			"reference_docname": task.name,
			"redirect_to_doctype": task.reference_doctype,
			"redirect_to_docname": task.reference_docname,
		}
	)
