import re
from datetime import datetime

import frappe
from frappe import _
from frappe.utils import add_to_date, now_datetime

from crm.fcrm.doctype.crm_notification.crm_notification import notify_user


def after_insert(doc, method):
	if doc.reference_type in ["CRM Lead", "CRM Deal"] and doc.reference_name and doc.allocated_to:
		fieldname = "lead_owner" if doc.reference_type == "CRM Lead" else "deal_owner"
		owner = frappe.db.get_value(doc.reference_type, doc.reference_name, fieldname)
		if not owner:
			frappe.db.set_value(
				doc.reference_type, doc.reference_name, fieldname, doc.allocated_to, update_modified=False
			)

	if doc.reference_type in ["CRM Lead", "CRM Deal", "CRM Task"] and doc.reference_name and doc.allocated_to:
		notify_assigned_user(doc)


def on_update(doc, method):
	if (
		doc.has_value_changed("status")
		and doc.status == "Cancelled"
		and doc.reference_type in ["CRM Lead", "CRM Deal", "CRM Task"]
		and doc.reference_name
		and doc.allocated_to
	):
		notify_assigned_user(doc, is_cancelled=True)


def notify_assigned_user(doc, is_cancelled=False):
	_doc = frappe.get_doc(doc.reference_type, doc.reference_name)
	owner = frappe.get_cached_value("User", frappe.session.user, "full_name")
	notification_text = get_notification_text(owner, doc, _doc, is_cancelled)

	message = (
		_("Your assignment on {0} {1} has been removed by {2}").format(
			doc.reference_type, doc.reference_name, owner
		)
		if is_cancelled
		else _("{0} assigned a {1} {2} to you").format(owner, doc.reference_type, doc.reference_name)
	)

	redirect_to_doctype, redirect_to_name = get_redirect_to_doc(doc)

	notify_user(
		{
			"owner": frappe.session.user,
			"assigned_to": doc.allocated_to,
			"notification_type": "Assignment",
			"message": message,
			"notification_text": notification_text,
			"reference_doctype": doc.reference_type,
			"reference_docname": doc.reference_name,
			"redirect_to_doctype": redirect_to_doctype,
			"redirect_to_docname": redirect_to_name,
		}
	)


def get_notification_text(owner, doc, reference_doc, is_cancelled=False):
	name = doc.reference_name
	doctype = doc.reference_type

	if doctype.startswith("CRM "):
		doctype = doctype[4:].lower()

	if doctype in ["lead", "deal"]:
		name = (
			reference_doc.lead_name or name
			if doctype == "lead"
			else reference_doc.organization or reference_doc.lead_name or name
		)

		if is_cancelled:
			return f"""
                <div class="mb-2 leading-5 text-ink-gray-5">
                    <span>{
				_("Your assignment on {0} {1} has been removed by {2}").format(
					doctype,
					f'<span class="font-medium text-ink-gray-9">{name}</span>',
					f'<span class="font-medium text-ink-gray-9">{owner}</span>',
				)
			}</span>
                </div>
            """

		return f"""
            <div class="mb-2 leading-5 text-ink-gray-5">
                <span class="font-medium text-ink-gray-9">{owner}</span>
                <span>{
			_("assigned a {0} {1} to you").format(
				doctype, f'<span class="font-medium text-ink-gray-9">{name}</span>'
			)
		}</span>
            </div>
        """

	if doctype == "task":
		if is_cancelled:
			return f"""
                <div class="mb-2 leading-5 text-ink-gray-5">
                    <span>{
				_("Your assignment on task {0} has been removed by {1}").format(
					f'<span class="font-medium text-ink-gray-9">{reference_doc.title}</span>',
					f'<span class="font-medium text-ink-gray-9">{owner}</span>',
				)
			}</span>
                </div>
            """
		return f"""
            <div class="mb-2 leading-5 text-ink-gray-5">
                <span class="font-medium text-ink-gray-9">{owner}</span>
                <span>{
			_("assigned a new task {0} to you").format(
				f'<span class="font-medium text-ink-gray-9">{reference_doc.title}</span>'
			)
		}</span>
            </div>
        """


def get_redirect_to_doc(doc):
	if doc.reference_type == "CRM Task":
		reference_doc = frappe.get_doc(doc.reference_type, doc.reference_name)
		return reference_doc.reference_doctype, reference_doc.reference_docname

	return doc.reference_type, doc.reference_name


TASK_REMINDER_OFFSETS = {
	"hours": [{"value": 1, "label": "1 hour"}],
	"days": [{"value": 1, "label": "1 day"}],
}


def trigger_hourly_task_reminders():
	_process_task_reminders("hours")


def trigger_daily_task_reminders():
	_process_task_reminders("days")


def _process_task_reminders(interval: str):
	"""
	Process task reminders for a given interval.

	Queries all open CRM Tasks with a due_date and assigned_to user,
	calculates trigger windows, deduplicates, and sends both in-app
	and email notifications.

	Args:
		interval (str): 'hours' or 'days'
	"""

	current_time = now_datetime()
	offsets = TASK_REMINDER_OFFSETS.get(interval, [])
	if not offsets:
		return

	tasks = frappe.get_all(
		"CRM Task",
		filters={
			"status": ["not in", ["Done", "Canceled"]],
			"due_date": ["is", "set"],
			"assigned_to": ["is", "set"],
		},
		fields=[
			"name",
			"title",
			"due_date",
			"assigned_to",
			"priority",
			"status",
			"reference_doctype",
			"reference_docname",
		],
	)

	for task in tasks:
		for offset in offsets:
			try:
				_process_single_task_reminder(task, offset, interval, current_time)
			except Exception as e:
				frappe.log_error(f"Error processing {interval} reminder for task {task.name}: {e!s}")


def _process_single_task_reminder(task: dict, offset: dict, interval: str, current_time: datetime):
	due_date = task.due_date
	if not isinstance(due_date, datetime):
		due_date = frappe.utils.get_datetime(due_date)

	if interval == "days":
		target_date = add_to_date(due_date, days=-offset["value"]).date()
		if current_time.date() != target_date:
			return
	else:
		interval_kwargs = _get_interval_kwargs(interval, offset["value"])
		trigger_time = add_to_date(due_date, **interval_kwargs)

		window = _get_trigger_window_duration(interval)
		window_start = add_to_date(trigger_time, **{k: -v for k, v in window.items()})
		window_end = add_to_date(trigger_time, **window)
		if not (window_start <= current_time <= window_end):
			return

	reminder_key = f"task_reminder_{interval}_{offset['value']}"
	existing = frappe.db.exists(
		"CRM Notification",
		{
			"type": "Task",
			"notification_type_doctype": "CRM Task",
			"notification_type_doc": str(task.name),
			"to_user": task.assigned_to,
			"message": ["like", f"%{reminder_key}%"],
		},
	)
	if existing:
		return

	# Send in-app notification
	_send_task_inapp_notification(task, offset, reminder_key)

	# Send email notification
	_send_task_email_notification(task, offset)


def _get_interval_kwargs(interval, before_value):
	"""
	Get the appropriate keyword arguments for add_to_date based on interval type.

	Args:
		interval (str): The interval type ('minutes', 'hours', 'days', 'weeks')
		before_value (int): How many units before the event

	Returns:
		dict: Keyword arguments for add_to_date with negative values
	"""
	interval_mapping = {
		"minutes": {"minutes": -before_value},
		"hours": {"hours": -before_value},
		"days": {"days": -before_value},
		"weeks": {"weeks": -before_value},
	}

	return interval_mapping.get(interval, {"hours": -before_value})


def _get_trigger_window_duration(interval):
	"""
	Get the trigger window duration based on interval type.

	Args:
		interval (str): The interval type ('minutes', 'hours', 'days', 'weeks')

	Returns:
		dict: Window duration to be used symmetrically around the trigger time
	"""
	window_mapping = {
		"minutes": {"minutes": 5},
		"hours": {"hours": 1},
		"days": {"hours": 8},
		"weeks": {"days": 4},
	}

	return window_mapping.get(interval, {"hours": 1})


def _send_task_inapp_notification(task: dict, offset: dict, reminder_key: str):
	notification_text = f"""
		<div class="mb-2 leading-5 text-ink-gray-5">
			Task <span class="font-medium text-ink-gray-9">{task.title}</span>
			is due in {offset["label"]}.</span>
		</div>
	"""

	reference_doctype = (
		task.reference_doctype if task.reference_doctype and task.reference_docname else "CRM Task"
	)
	reference_name = (
		task.reference_docname if task.reference_doctype and task.reference_docname else str(task.name)
	)

	values = frappe._dict(
		doctype="CRM Notification",
		from_user=task.assigned_to,
		to_user=task.assigned_to,
		type="Task",
		message=f"Task '{task.title}' is due in {offset['label']}. [{reminder_key}]",
		notification_text=notification_text,
		notification_type_doctype="CRM Task",
		notification_type_doc=str(task.name),
		reference_doctype=reference_doctype,
		reference_name=reference_name,
	)

	frappe.get_doc(values).insert(ignore_permissions=True)


def _strip_root_p_tags(text: str):
	if not text:
		return text
	text = str(text).strip()
	if text.startswith("<p>") and text.endswith("</p>"):
		text = text[3:-4]
		text = re.sub(r"</p>\s*<p>", "<br><br>", text)
	return text


def _format_due_date_for_email(due_date: str):
	dt = frappe.utils.get_datetime(due_date)
	am_pm = "AM" if dt.hour < 12 else "PM"
	hour = dt.hour % 12 or 12
	return f"{dt.strftime('%b')} {dt.day}, {dt.year}, {hour}:{dt.strftime('%M')} {am_pm}"


def _send_task_email_notification(task: dict, offset: dict):
	recipient = task.assigned_to
	if not recipient:
		return

	subject = f"Task Reminder: {task.title} — due in {offset['label']}"

	assigned_to_name = frappe.db.get_value("User", recipient, "full_name") or recipient
	task_doc = frappe.get_doc("CRM Task", task.name)
	brand_logo = frappe.db.get_single_value("FCRM Settings", "brand_logo") or "/assets/crm/images/logo.png"

	site_url = frappe.utils.get_url()
	task_url = f"{site_url}/crm/tasks/view/list?open={task.name}"

	# nosemgrep
	message = frappe.render_template(
		"crm/templates/emails/task_reminder.html",
		{
			"task_title": task.title,
			"due_date": _format_due_date_for_email(task.due_date),
			"time_remaining": offset["label"],
			"assigned_to_name": assigned_to_name,
			"description": _strip_root_p_tags(task_doc.description),
			"task_url": task_url,
			"brand_logo": brand_logo,
		},
	)

	frappe.sendmail(
		recipients=[recipient],
		subject=subject,
		message=message,
		reference_doctype="CRM Task",
		reference_name=str(task.name),
		now=True,
	)
