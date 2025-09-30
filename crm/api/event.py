import frappe
from frappe.utils import add_to_date, now_datetime


def trigger_offset_event_notifications():
	pass


def trigger_hourly_event_notifications():
	"""
	Trigger event notifications for all events with hourly interval notifications.

	This function:
	1. Fetches all Event Notifications with interval = 'hours'
	2. Calculates the trigger time based on event start time and before_hours
	3. Checks if current time is within the trigger window
	4. Sends email or system notifications based on notification type
	5. Prevents duplicate notifications by checking existing logs
	"""

	# Skip if running in import or patch mode
	if frappe.flags.in_import or frappe.flags.in_patch:
		return

	# Get current datetime
	current_time = now_datetime()

	# Query all Event Notifications with interval = 'hours'
	# Only get events that haven't started yet (starts_on >= current_time)
	notifications = frappe.db.sql(
		"""
		SELECT
			en.parent as event_name,
			en.type as notification_type,
			en.before as before_hours,
			en.time as time_of_day,
			e.subject,
			e.starts_on,
			e.ends_on,
			e.owner,
			e.description,
			e.all_day as all_day_event
		FROM `tabEvent Notifications` en
		JOIN `tabEvent` e ON en.parent = e.name
		WHERE en.interval = 'hours'
		AND e.starts_on >= %s
		AND e.status != 'Cancelled'
		ORDER BY e.starts_on
	""",
		(current_time,),
		as_dict=True,
	)

	frappe.logger().info(f"Found {len(notifications)} hourly event notifications to process")

	for notification in notifications:
		try:
			event_start = notification.starts_on
			before_hours = notification.before_hours or 1

			# Calculate the notification trigger time
			# If time_of_day is specified, use it; otherwise use event start time minus before_hours
			if notification.all_day_event and notification.time_of_day:
				# Create trigger datetime using the specified time
				# The trigger date should be before_hours before the event
				from datetime import datetime, timedelta

				trigger_date = event_start.date() - timedelta(hours=before_hours // 24)
				if before_hours % 24:
					# If not a full day offset, use the same date
					trigger_date = event_start.date()

				trigger_datetime = datetime.combine(trigger_date, notification.time_of_day)
			else:
				# Simply subtract before_hours from event start time
				trigger_datetime = add_to_date(event_start, hours=-before_hours)

			# Check if current time is within the trigger window (1 hour window for hourly notifications)
			trigger_window_start = trigger_datetime
			trigger_window_end = add_to_date(trigger_datetime, hours=1)

			if not (trigger_window_start <= current_time <= trigger_window_end):
				continue

			# Check if we've already sent this notification recently
			# Use a unique identifier combining event name, notification type, and trigger time
			notification_subject = f"Event Reminder: {notification.subject}"
			existing_log = frappe.db.exists(
				"Notification Log",
				{
					"document_type": "Event",
					"document_name": notification.event_name,
					"subject": notification_subject,
					"creation": (">=", add_to_date(current_time, hours=-2)),
				},
			)

			if existing_log:
				frappe.logger().debug(f"Notification already sent for event: {notification.event_name}")
				continue

			# Process the notification based on type
			if notification.notification_type == "Email":
				_send_email_notification(notification, event_start, before_hours, notification_subject)
			elif notification.notification_type == "Notification":
				_send_system_notification(notification)

		except Exception as e:
			frappe.logger().error(
				f"Error processing notification for event {notification.get('event_name', 'Unknown')}: {e!s}"
			)
			continue


def trigger_daily_event_notifications():
	pass


def trigger_weekly_event_notifications():
	pass


def _send_email_notification(notification, event_start, before_hours, subject):
	"""Send email notification for an event"""

	try:
		recipients = []

		# Add event owner
		if notification.owner:
			recipients.append(notification.owner)

		# Get event participants
		event_doc = frappe.get_doc("Event", notification.event_name)
		for participant in event_doc.get("event_participants", []):
			if hasattr(participant, "email") and participant.email:
				recipients.append(participant.email)

		# Remove duplicates
		recipients = list(set(recipients))

		if not recipients:
			frappe.logger().warning(f"No recipients found for event notification: {notification.event_name}")
			return

		message = f"""
		<div style="font-family: Arial, sans-serif; max-width: 600px;">
			<h2 style="color: #333;">Event Reminder</h2>
			<p>This is a reminder for your upcoming event:</p>
			<div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0;">
				<h3 style="margin: 0; color: #007bff;">{notification.subject}</h3>
				{f'<p style="margin: 10px 0; color: #666;">{notification.description}</p>' if notification.description else ''}
				<p style="margin: 5px 0;"><strong>Start Time:</strong> {event_start.strftime('%Y-%m-%d %H:%M:%S')}</p>
				<p style="margin: 5px 0;"><strong>Time Remaining:</strong> {before_hours} hour(s)</p>
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

		frappe.logger().info(
			f"Email notification sent for event: {notification.event_name} to {len(recipients)} recipients"
		)

	except Exception as e:
		frappe.logger().error(f"Failed to send email for event {notification.event_name}: {e!s}")


def _send_system_notification(notification):
	"""Send system notification for an event"""
	frappe.publish_realtime("event_notification", notification)
