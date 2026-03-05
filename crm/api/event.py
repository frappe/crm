"""
Event notification handling for CRM.

This module handles event notifications for the CRM system, supporting both:
1. Custom event notifications set on individual events
2. Global default notifications from CRM Settings for events without custom notifications

The notification system processes events that are either:
- Starting from now or in the future (normal case)
- Currently in progress (between starts_on and ends_on) to handle delayed notifications

Global notifications are configured in CRM Settings under the Calendar tab and are applied
to events that don't have custom notifications set. This ensures all events can receive
reminders even if users don't configure them individually.
"""

import re
from datetime import datetime, timedelta

import frappe
from frappe.utils import add_to_date, now_datetime


def trigger_offset_event_notifications():
	"""Trigger event notifications for offset-based intervals (minutes)."""
	_process_event_notifications_by_interval("minutes")
	_process_event_notifications_by_interval("hours")


def trigger_hourly_event_notifications():
	"""Trigger event notifications for hourly intervals."""
	_process_event_notifications_by_interval("hours")


def trigger_daily_event_notifications():
	"""Trigger event notifications for daily intervals."""
	_process_event_notifications_by_interval("days")


def trigger_weekly_event_notifications():
	"""Trigger event notifications for weekly intervals."""
	_process_event_notifications_by_interval("weeks")


def _process_event_notifications_by_interval(interval):
	"""
	Process event notifications for a specific interval.

	Args:
		interval (str): The interval type ('minutes', 'hours', 'days', 'weeks')
	"""

	if frappe.flags.in_import or frappe.flags.in_patch:
		return

	current_time = now_datetime()
	current_user = frappe.session.user
	all_events_data = frappe.db.sql(
		"""
		SELECT
			e.name as event_name,
			e.subject,
			e.starts_on,
			e.ends_on,
			e.owner,
			e.description,
			e.all_day as all_day_event,
			en.type as notification_type,
			en.before as before_value,
			en.time as time_of_day,
			en.interval as notification_interval,
			ep.email as participant_email,
			ep_all.participant_emails_csv,
			CASE WHEN en.parent IS NULL THEN 0 ELSE 1 END as has_custom_notifications
		FROM `tabEvent` e
		LEFT JOIN `tabEvent Notifications` en ON e.name = en.parent AND en.interval = %s
		LEFT JOIN `tabEvent Participants` ep ON e.name = ep.parent AND ep.email = %s
		LEFT JOIN (
			SELECT parent, GROUP_CONCAT(email) AS participant_emails_csv
			FROM `tabEvent Participants`
			GROUP BY parent
		) AS ep_all ON ep_all.parent = e.name
		WHERE (e.starts_on >= %s OR (%s >= e.starts_on AND %s < e.ends_on))
		AND (e.owner = %s OR ep.email = %s)
		AND e.status != 'Cancelled'
		ORDER BY e.starts_on, e.name
	""",
		(interval, current_user, current_time, current_time, current_time, current_user, current_user),
		as_dict=True,
	)

	for event_data in all_events_data:
		participant_emails_csv = event_data.pop("participant_emails_csv", None)
		event_data["event_participants"] = _split_participant_emails(participant_emails_csv)

	notifications = _process_unified_event_data(all_events_data, interval)

	for notification in notifications:
		try:
			event_start = notification.get("starts_on")
			event_end = notification.get("ends_on")
			before_value = notification.get("before_value", 1)

			trigger_datetime = _calculate_trigger_datetime(
				event_start,
				before_value,
				interval,
				notification.get("all_day_event"),
				notification.get("time_of_day"),
			)

			event_is_in_progress = event_start <= current_time < event_end
			trigger_time_passed = current_time > trigger_datetime

			if event_is_in_progress and trigger_time_passed:
				trigger_window_start = trigger_datetime
				trigger_window_end = event_end
			else:
				window_duration = _get_trigger_window_duration(interval)
				trigger_window_start = add_to_date(
					trigger_datetime, **{k: -v for k, v in window_duration.items()}
				)
				trigger_window_end = add_to_date(trigger_datetime, **window_duration)

			if not (trigger_window_start <= current_time <= trigger_window_end):
				continue

			if notification.get("notification_type") == "Email":
				_send_email_notification(notification, event_start, before_value, interval)
			elif notification.get("notification_type") == "Notification":
				_send_system_notification(notification)

		except Exception as e:
			frappe.log_error(
				f"Error processing {interval} notification for event {notification.get('event_name', 'Unknown')}: {e!s}"
			)
			continue


def _process_unified_event_data(all_events_data, interval):
	"""
	Process unified event data that includes both events with and without custom notifications.

	Args:
		all_events_data (list): List of event data from the unified query
		interval (str): The interval type ('minutes', 'hours', 'days', 'weeks')

	Returns:
		list: List of processed notifications ready for sending
	"""
	notifications = []
	events_without_notifications = []

	for event_data in all_events_data:
		if event_data.get("has_custom_notifications") == 1:
			notifications.append(event_data)
		else:
			event_key = event_data.get("event_name")
			if not any(e.get("event_name") == event_key for e in events_without_notifications):
				events_without_notifications.append(event_data)
	if events_without_notifications:
		global_notifications = _apply_global_notifications_to_events(events_without_notifications, interval)
		notifications.extend(global_notifications)

	return notifications


def _apply_global_notifications_to_events(events_without_notifications, interval):
	"""
	Apply global CRM Settings notifications to events that don't have custom notifications.

	Args:
		events_without_notifications (list): List of events without custom notifications
		interval (str): The interval type ('minutes', 'hours', 'days', 'weeks')

	Returns:
		list: List of notification dictionaries using global settings
	"""

	fcrm_settings = frappe.get_single("FCRM Settings")
	global_notifications = []
	if hasattr(fcrm_settings, "event_notifications"):
		for notification in fcrm_settings.event_notifications:
			if notification.interval == interval:
				notification._table_type = "regular"
				global_notifications.append(notification)

	if hasattr(fcrm_settings, "all_day_event_notifications"):
		for notification in fcrm_settings.all_day_event_notifications:
			if notification.interval == interval:
				notification._table_type = "all_day"
				global_notifications.append(notification)

	if not global_notifications:
		return []
	notifications = []
	for event in events_without_notifications:
		for global_notification in global_notifications:
			if (global_notification._table_type == "all_day" and not event.all_day_event) or (
				global_notification._table_type == "regular" and event.all_day_event
			):
				continue

			notification = {
				"event_name": event.event_name,
				"notification_type": global_notification.type,
				"before_value": global_notification.before,
				"time_of_day": global_notification.time,
				"subject": event.subject,
				"starts_on": event.starts_on,
				"ends_on": event.ends_on,
				"owner": event.owner,
				"description": event.description,
				"all_day_event": event.all_day_event,
				"event_participants": event.get("event_participants", []),
			}
			notifications.append(notification)

	return notifications


def _calculate_trigger_datetime(event_start, before_value, interval, all_day_event, time_of_day):
	"""
	Calculate when the notification should be triggered based on event start time and interval.

	Args:
		event_start (datetime): Event start datetime
		before_value (int): How many units before the event
		interval (str): The interval type ('minutes', 'hours', 'days', 'weeks')
		all_day_event (bool): Whether this is an all-day event
		time_of_day (time): Specific time to send notification for all-day events

	Returns:
		datetime: When the notification should be triggered
	"""

	if all_day_event and time_of_day and interval in ["days", "weeks"]:
		if interval == "days":
			trigger_date = event_start.date() - timedelta(days=before_value)
		elif interval == "weeks":
			trigger_date = event_start.date() - timedelta(weeks=before_value)

		trigger_datetime = datetime.combine(trigger_date, time_of_day)
	else:
		interval_kwargs = _get_interval_kwargs(interval, before_value)
		trigger_datetime = add_to_date(event_start, **interval_kwargs)

	return trigger_datetime


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


def _split_participant_emails(participant_emails_csv):
	"""Return a clean list of participant emails from a comma-separated string."""

	if not participant_emails_csv:
		return []

	return [email.strip() for email in participant_emails_csv.split(",") if email and email.strip()]


def _send_email_notification(notification, event_start, before_value, interval):
	"""Send email notification for an event"""

	try:
		recipients = set()
		subject = f"Event Reminder: {notification.subject}"

		if notification.owner and notification.owner != "Administrator":
			recipients.add(notification.owner)

		participant_emails = notification.get("event_participants") or []
		if participant_emails:
			recipients.update(participant_emails)
		else:
			event_doc = frappe.get_doc("Event", notification.event_name)
			for participant in event_doc.get("event_participants", []):
				email = getattr(participant, "email", None)
				if email:
					recipients.add(email)

		recipients = [email for email in recipients if email]

		if not recipients:
			return
		time_remaining_text = _format_time_remaining(before_value, interval)

		message = f"""
		<div style="font-family: Arial, sans-serif; max-width: 600px;">
			<h2 style="color: #333;">Event Reminder</h2>
			<p>This is a reminder for your upcoming event:</p>
			<div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0;">
				<h3 style="margin: 0; color: #007bff;">{notification.subject}</h3>
				{f'<p style="margin: 10px 0; color: #666;">{notification.description}</p>' if notification.description else ""}
				<p style="margin: 5px 0;"><strong>Start Time:</strong> {event_start.strftime("%Y-%m-%d %H:%M:%S")}</p>
				<p style="margin: 5px 0;"><strong>Time Remaining:</strong> {time_remaining_text}</p>
			</div>
			<p style="color: #666; font-size: 12px;">This is an automated reminder from your calendar system.</p>
		</div>
		"""

		frappe.sendmail(
			recipients=recipients,
			subject=subject,
			message=message,
			reference_doctype="Event",
			reference_name=notification.event_name,
			now=True,
		)

	except Exception as e:
		frappe.log_error(f"Failed to send email for event {notification.event_name}: {e!s}")


def _format_time_remaining(before_value, interval):
	"""
	Format the time remaining message based on the interval and before value.

	Args:
		before_value (int): The number of units before the event
		interval (str): The interval type ('minutes', 'hours', 'days', 'weeks')

	Returns:
		str: Formatted time remaining message
	"""
	interval_labels = {"minutes": "minute(s)", "hours": "hour(s)", "days": "day(s)", "weeks": "week(s)"}

	interval_label = interval_labels.get(interval, "unit(s)")
	return f"{before_value} {interval_label}"


def _send_system_notification(notification):
	"""Send system notification for an event"""
	frappe.publish_realtime("event_notification", notification)


TASK_REMINDER_OFFSETS = {
	"hours": [{"value": 1, "label": "1 hour"}],
	"days": [{"value": 1, "label": "1 day"}],
}


def send_hourly_task_reminders():
	_process_task_reminders("hours")


def send_daily_task_reminders():
	_process_task_reminders("days")


def _process_task_reminders(interval):
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


def _process_single_task_reminder(task, offset, interval, current_time):
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


def _send_task_inapp_notification(task, offset, reminder_key):
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


def _strip_root_p_tags(text):
	if not text:
		return text
	text = str(text).strip()
	if text.startswith("<p>") and text.endswith("</p>"):
		text = text[3:-4]
		text = re.sub(r"</p>\s*<p>", "<br><br>", text)
	return text


def _format_due_date_for_email(due_date):
	dt = frappe.utils.get_datetime(due_date)
	am_pm = "AM" if dt.hour < 12 else "PM"
	hour = dt.hour % 12 or 12
	return f"{dt.strftime('%b')} {dt.day}, {dt.year}, {hour}:{dt.strftime('%M')} {am_pm}"


def _send_task_email_notification(task, offset):
	recipient = task.assigned_to
	if not recipient:
		return

	subject = f"Task Reminder: {task.title} — due in {offset['label']}"

	assigned_to_name = frappe.db.get_value("User", recipient, "full_name") or recipient
	task_doc = frappe.get_doc("CRM Task", task.name)
	brand_logo = (
		frappe.db.get_value("FCRM Settings", "FCRM Settings", "brand_logo") or "/assets/crm/images/logo.png"
	)

	site_url = frappe.utils.get_url()
	task_url = f"{site_url}/crm/tasks/view/list?open={task.name}"

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
