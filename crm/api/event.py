"""
Event notification handling for CRM.

This module handles event notifications for the CRM system, supporting both:
1. Custom event notifications set on individual events
2. Global default notifications from CRM Settings for events without custom notifications

Global notifications are configured in CRM Settings under the Calendar tab and are applied
to events that don't have custom notifications set. This ensures all events can receive
reminders even if users don't configure them individually.
"""

from datetime import datetime, timedelta

import frappe
from frappe.utils import add_to_date, now_datetime


def trigger_offset_event_notifications():
	"""
	Trigger event notifications for specific offset-based intervals.

	This function processes notifications for offset times e.g., 30 minutes before event.
	"""
	_process_event_notifications_by_interval("minutes")


def trigger_hourly_event_notifications():
	"""
	Trigger event notifications for all events with hourly interval notifications.

	This function processes notifications for hourly intervals e.g., 1 hour before event.
	"""
	_process_event_notifications_by_interval("hours")


def trigger_daily_event_notifications():
	"""
	Trigger event notifications for all events with daily interval notifications.

	This function processes notifications for daily intervals e.g., 1 day before event.
	"""
	_process_event_notifications_by_interval("days")


def trigger_weekly_event_notifications():
	"""
	Trigger event notifications for all events with weekly interval notifications.

	This function processes notifications for weekly intervals e.g., 1 week before event.
	"""
	_process_event_notifications_by_interval("weeks")


def _process_event_notifications_by_interval(interval):
	"""
	Generic function to process event notifications for a specific interval.

	Args:
		interval (str): The interval type ('minutes', 'hours', 'days', 'weeks')
	"""

	# Skip if running in import or patch mode
	if frappe.flags.in_import or frappe.flags.in_patch:
		return

	# Get current datetime
	current_time = now_datetime()

	# Fetch all events starting from now that have notifications for the given interval
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
			CASE WHEN en.parent IS NULL THEN 0 ELSE 1 END as has_custom_notifications
		FROM `tabEvent` e
		LEFT JOIN `tabEvent Notifications` en ON e.name = en.parent AND en.interval = %s
		WHERE e.starts_on >= %s
		AND e.status != 'Cancelled'
		ORDER BY e.starts_on, e.name
	""",
		(interval, current_time),
		as_dict=True,
	)

	notifications = _process_unified_event_data(all_events_data, interval)

	for notification in notifications:
		try:
			event_start = notification.get("starts_on")
			event_end = notification.get("ends_on")
			before_value = notification.get("before_value", 1)

			# Calculate the notification trigger time based on interval
			trigger_datetime = _calculate_trigger_datetime(
				event_start,
				before_value,
				interval,
				notification.get("all_day_event"),
				notification.get("time_of_day"),
			)

			# Calculate trigger window based on interval and event duration
			# Before window: fixed based on interval, After window: based on event duration
			trigger_window_before, trigger_window_after = _get_trigger_window_durations(
				interval, event_start, event_end
			)

			# Create window before the trigger time (negative duration)
			trigger_window_start = add_to_date(
				trigger_datetime, **{k: -v for k, v in trigger_window_before.items()}
			)
			# Create window after the trigger time (positive duration)
			trigger_window_end = add_to_date(trigger_datetime, **trigger_window_after)

			if not (trigger_window_start <= current_time <= trigger_window_end):
				continue

			# Process the notification based on type
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

	# Separate events with custom notifications from those without
	for event_data in all_events_data:
		if event_data.get("has_custom_notifications") == 1:
			# Event has custom notifications - add directly
			notifications.append(event_data)
		else:
			# Track events without custom notifications for global processing
			# Only add unique events (avoid duplicates from LEFT JOIN)
			event_key = event_data.get("event_name")
			if not any(e.get("event_name") == event_key for e in events_without_notifications):
				events_without_notifications.append(event_data)

	# Process events without custom notifications using global settings
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

	# Get appropriate global notifications based on interval
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

	# If no global notifications are set for this interval, return empty list
	if not global_notifications:
		return []

	# Create notification records for each event using global settings
	notifications = []
	for event in events_without_notifications:
		for global_notification in global_notifications:
			# Only apply all-day notifications to all-day events, and regular notifications to non-all-day events
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
		# For all-day events with specified time, calculate the trigger date and combine with time
		if interval == "days":
			trigger_date = event_start.date() - timedelta(days=before_value)
		elif interval == "weeks":
			trigger_date = event_start.date() - timedelta(weeks=before_value)

		trigger_datetime = datetime.combine(trigger_date, time_of_day)
	else:
		# For regular events or when no specific time is set, subtract the interval from event start
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


def _get_trigger_window_durations(interval, event_start=None, event_end=None):
	"""
	Get the trigger window durations (before and after) based on interval type.

	This creates a window both before and after the calculated trigger time
	to handle system delays, downtime, or processing issues.

	The before window is fixed based on interval type.
	The after window is calculated as a percentage of the event duration,
	with fallback to fixed durations if event duration cannot be determined.

	Args:
		interval (str): The interval type ('minutes', 'hours', 'days', 'weeks')
		event_start (datetime, optional): Event start time
		event_end (datetime, optional): Event end time

	Returns:
		tuple: (before_window_duration, after_window_duration) as dictionaries
	"""
	# Fixed before windows based on interval type
	before_window_mapping = {
		"minutes": {"minutes": 5},
		"hours": {"hours": 1},
		"days": {"hours": 8},
		"weeks": {"days": 4},
	}

	before_window = before_window_mapping.get(interval, {"hours": 1})

	# Calculate after window based on event duration
	after_window = _calculate_after_window_from_event_duration(event_start, event_end, interval)

	return before_window, after_window


def _calculate_after_window_from_event_duration(event_start, event_end, interval):
	"""
	Calculate the after window duration based on event duration.

	The after window is calculated as a percentage of the event duration:
	- 50% of event duration for all intervals (more responsive)

	Args:
		event_start (datetime): Event start time
		event_end (datetime): Event end time
		interval (str): The interval type ('minutes', 'hours', 'days', 'weeks')

	Returns:
		dict: Duration for the after window
	"""
	# If we don't have both start and end times, use fallback
	if not event_start or not event_end:
		return {"minutes": 30}

	# Calculate event duration in minutes
	try:
		event_duration_seconds = (event_end - event_start).total_seconds()
		event_duration_minutes = event_duration_seconds / 60

		# For very short events (less than 5 minutes), use minimum after window
		if event_duration_minutes < 5:
			return {"minutes": 2}

		after_window_minutes = int(event_duration_minutes * 0.5)

		# Cap the maximum after window based on interval
		max_after_windows = {
			"minutes": 15,  # Max 15 minutes for minute-based
			"hours": 30,  # Max 30 minutes for hourly
			"days": 60,  # Max 1 hour for daily
			"weeks": 60,  # Max 1 hour for weekly
		}

		max_after = max_after_windows.get(interval, 30)
		after_window_minutes = min(after_window_minutes, max_after)

		# Ensure minimum after window of 1 minute
		after_window_minutes = max(after_window_minutes, 1)

		# Convert to appropriate time unit
		if after_window_minutes >= 60:  # 1 hour or more
			return {"hours": int(after_window_minutes / 60)}
		else:
			return {"minutes": after_window_minutes}

	except Exception:
		# If any error occurs, fall back to default durations
		return {"minutes": 30}


def _send_email_notification(notification, event_start, before_value, interval):
	"""Send email notification for an event"""

	try:
		recipients = []
		subject = f"Event Reminder: {notification.subject}"

		# Add event owner
		if notification.owner and notification.owner != "Administrator":
			recipients.append(notification.owner)

		# Get event participants
		event_doc = frappe.get_doc("Event", notification.event_name)
		for participant in event_doc.get("event_participants", []):
			if hasattr(participant, "email") and participant.email:
				recipients.append(participant.email)

		# Remove duplicates
		recipients = list(set(recipients))

		if not recipients:
			return

		# Format time remaining message based on interval
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
