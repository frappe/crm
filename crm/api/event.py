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

	# Query all Event Notifications with the specified interval
	# Only get events that haven't started yet (starts_on >= current_time)
	notifications = frappe.db.sql(
		"""
		SELECT
			en.parent as event_name,
			en.type as notification_type,
			en.before as before_value,
			en.time as time_of_day,
			e.subject,
			e.starts_on,
			e.ends_on,
			e.owner,
			e.description,
			e.all_day as all_day_event
		FROM `tabEvent Notifications` en
		JOIN `tabEvent` e ON en.parent = e.name
		WHERE en.interval = %s
		AND e.starts_on >= %s
		AND e.status != 'Cancelled'
		ORDER BY e.starts_on
	""",
		(interval, current_time),
		as_dict=True,
	)

	for notification in notifications:
		try:
			event_start = notification.starts_on
			before_value = notification.before_value or 1

			# Calculate the notification trigger time based on interval
			trigger_datetime = _calculate_trigger_datetime(
				event_start, before_value, interval, notification.all_day_event, notification.time_of_day
			)

			# Calculate trigger window based on interval
			trigger_window_duration = _get_trigger_window_duration(interval)
			trigger_window_start = trigger_datetime
			trigger_window_end = add_to_date(trigger_datetime, **trigger_window_duration)

			if not (trigger_window_start <= current_time <= trigger_window_end):
				continue

			# Process the notification based on type
			if notification.notification_type == "Email":
				_send_email_notification(notification, event_start, before_value, interval)
			elif notification.notification_type == "Notification":
				_send_system_notification(notification)

		except Exception as e:
			frappe.log_error(
				f"Error processing {interval} notification for event {notification.get('event_name', 'Unknown')}: {e!s}"
			)
			continue


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


def _get_trigger_window_duration(interval):
	"""
	Get the trigger window duration based on interval type.

	Args:
		interval (str): The interval type ('minutes', 'hours', 'days', 'weeks')

	Returns:
		dict: Duration for the trigger window
	"""
	window_mapping = {
		"minutes": {"minutes": 5},  # 5-minute window for minute-based notifications
		"hours": {"hours": 1},  # 1-hour window for hourly notifications
		"days": {"hours": 8},  # 8-hour window for daily notifications
		"weeks": {"days": 4},  # 4-day window for weekly notifications
	}

	return window_mapping.get(interval, {"hours": 1})


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
				{f'<p style="margin: 10px 0; color: #666;">{notification.description}</p>' if notification.description else ''}
				<p style="margin: 5px 0;"><strong>Start Time:</strong> {event_start.strftime('%Y-%m-%d %H:%M:%S')}</p>
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
