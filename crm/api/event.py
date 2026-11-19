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

import hashlib
import re
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.query_builder.functions import Max
from frappe.utils import add_to_date, cint, now_datetime


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
	scan_until = _get_scan_horizon(interval, current_time)
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
			ep_all.participant_emails_csv,
			CASE WHEN en.parent IS NULL THEN 0 ELSE 1 END as has_custom_notifications
		FROM `tabEvent` e
		LEFT JOIN `tabEvent Notifications` en ON e.name = en.parent AND en.interval = %s
		LEFT JOIN (
			SELECT parent, GROUP_CONCAT(email) AS participant_emails_csv
			FROM `tabEvent Participants`
			GROUP BY parent
		) AS ep_all ON ep_all.parent = e.name
		WHERE ((e.starts_on >= %s AND e.starts_on <= %s) OR (%s >= e.starts_on AND %s < e.ends_on))
		AND e.status != 'Cancelled'
		ORDER BY e.starts_on, e.name
	""",
		(interval, current_time, scan_until, current_time, current_time),
		as_dict=True,
	)

	for event_data in all_events_data:
		participant_emails_csv = event_data.pop("participant_emails_csv", None)
		event_data["event_participants"] = _split_participant_emails(participant_emails_csv)

	notifications = _process_unified_event_data(all_events_data, interval)

	for notification in notifications:
		frappe.db.savepoint("send_event_reminder")
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
				_send_system_notification(notification, interval)

		except Exception as e:
			# Drop the markers of a reminder that did not go out, so the next run retries it.
			frappe.db.rollback(save_point="send_event_reminder")
			frappe.log_error(
				f"Error processing {interval} notification for event {notification.get('event_name', 'Unknown')}: {e!s}"
			)
			continue


def _get_scan_horizon(interval, current_time):
	"""
	Latest event start whose reminder for this interval can fire now: the longest offset
	(event and CRM Settings rows share one table), the trigger window, and a day for
	all-day events, whose trigger is the start date at a time of day.
	"""

	notifications = frappe.qb.DocType("Event Notifications")
	longest_offset = (
		frappe.qb.from_(notifications)
		.select(Max(notifications.before))
		.where(notifications.interval == interval)
		.run()[0][0]
		or 0
	)

	horizon = add_to_date(current_time, **{interval: longest_offset})
	horizon = add_to_date(horizon, **_get_trigger_window_duration(interval))
	return add_to_date(horizon, days=1)


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


def _claim_new_recipients(notification, interval, recipients):
	"""
	Return the recipients that have not had this reminder yet, and record them as sent.

	The marker is per event start, reminder row and recipient. It is written before the
	send so that overlapping job runs cannot both send.
	"""

	new_recipients = []
	for recipient in recipients:
		key = _get_reminder_key(notification, interval, recipient)
		frappe.db.savepoint("claim_event_reminder")
		marker = frappe.new_doc("CRM Event Reminder Log")
		marker.update(
			{
				"reminder_key": key,
				"event": notification.get("event_name"),
				"recipient": recipient,
				"sent_on": now_datetime(),
			}
		)
		marker.set_new_name()
		marker.set_user_and_timestamp()
		try:
			# db_insert skips the realtime list update a normal insert publishes per marker.
			marker.db_insert()
		except frappe.DuplicateEntryError:
			frappe.db.rollback(save_point="claim_event_reminder")
			continue
		new_recipients.append(recipient)

	return new_recipients


def _get_reminder_key(notification, interval, recipient):
	parts = (
		notification.get("event_name"),
		notification.get("starts_on"),
		notification.get("notification_type"),
		interval,
		notification.get("before_value"),
		notification.get("time_of_day"),
		recipient,
	)
	return hashlib.sha256("|".join(str(part) for part in parts).encode()).hexdigest()


def purge_event_reminder_logs():
	"""Delete the markers of events that are gone or ended more than a day ago."""

	log = frappe.qb.DocType("CRM Event Reminder Log")
	event = frappe.qb.DocType("Event")
	cutoff = add_to_date(now_datetime(), days=-1)
	live_events = (
		frappe.qb.from_(event).select(event.name).where((event.ends_on > cutoff) | (event.starts_on > cutoff))
	)
	frappe.qb.from_(log).delete().where(log.event.notin(live_events)).run()


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

		recipients = _claim_new_recipients(
			notification, interval, sorted(email for email in recipients if email)
		)

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
		frappe.db.rollback(save_point="send_event_reminder")
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


def _send_system_notification(notification, interval):
	"""Send system notification for an event"""
	recipients = {notification.get("owner"), *notification.get("event_participants", [])}
	for user in _claim_new_recipients(notification, interval, sorted(recipients - {None})):
		frappe.publish_realtime("event_notification", notification, user=user)


# Seeing events. Frappe shows a private Event only to its owner and participants, so a
# meeting a host has on a lead (a booking, say) would be invisible on that lead to the
# rest of the team. These endpoints stand in for frappe.client.get_list on the CRM's
# event lists: anything the user may see as usual, plus events linked to a lead or deal
# the user can read. Writes still go through Frappe's own Event permissions.

EVENT_DOCTYPES = ("Event", "Event Participants", "Event Notifications")
MAX_EVENT_ROWS = 2000


@frappe.whitelist()
def get_event_list(
	doctype: str,
	fields: list | str | None = None,
	filters: dict | list | str | None = None,
	or_filters: dict | list | str | None = None,
	order_by: str | None = None,
	limit: int | None = None,
	limit_start: int = 0,
	parent: str | None = None,
	**kwargs,
) -> list[dict]:
	if doctype not in EVENT_DOCTYPES:
		frappe.throw(_("Not an event list"), frappe.PermissionError)
	frappe.has_permission("Event", "read", throw=True)
	limit = min(cint(limit) or MAX_EVENT_ROWS, MAX_EVENT_ROWS)
	fields = plain_fields(doctype, frappe.parse_json(fields) or ["*"])
	table = frappe.qb.DocType(doctype)
	event_of = table.name if doctype == "Event" else table.parent

	# Visibility is part of the query, so the caller's filters, order and limit only
	# ever see rows the user may read: no answer depends on a hidden row.
	query = frappe.get_all(
		doctype,
		fields=fields,
		filters=plain_filters(frappe.parse_json(filters)),
		or_filters=plain_filters(frappe.parse_json(or_filters)),
		order_by=plain_order_by(order_by) or "creation desc",
		limit_start=cint(limit_start),
		limit_page_length=limit,
		run=False,
	)
	rows = query.where(event_of.isin(visible_events())).run(as_dict=True)
	return add_booking_guests(rows) if doctype == "Event" else rows


def visible_events():
	"""Names of the events the user may see, as a subquery: by Frappe's own Event rules,
	or by reading the lead or deal the event is linked to."""
	Event = frappe.qb.DocType("Event")
	visible = Event.name.isin(frappe.get_list("Event", fields=["name"], limit_page_length=0, run=False))
	for doctype in ("CRM Lead", "CRM Deal"):
		readable = frappe.get_list(doctype, fields=["name"], limit_page_length=0, run=False)
		visible |= (Event.reference_doctype == doctype) & Event.reference_docname.isin(readable)
	return frappe.qb.from_(Event).select(Event.name).where(visible)


def plain_fields(doctype: str, fields: list) -> list[str]:
	"""Only the doctype's own columns: no aliases, child-table or linked fields that
	could read rows outside the visibility check."""
	columns = set(frappe.get_meta(doctype).get_valid_columns())
	for field in fields:
		if field != "*" and field not in columns:
			frappe.throw(_("Field not allowed: {0}").format(field), frappe.PermissionError)
	return fields


def plain_filters(filters):
	"""Only plain fields of the event doctypes. Frappe also takes `link.field`, which
	would read the linked record without checking the user may."""
	if isinstance(filters, dict):
		for field in filters:
			plain_filter_field(field)
	elif isinstance(filters, list | tuple):
		if filters and isinstance(filters[0], str) and filters[0].lower() not in ("and", "or"):
			# a condition: [field, ...] or, with 4 or more items, [doctype, field, ...]
			if len(filters) >= 4:
				if filters[0] not in EVENT_DOCTYPES:
					frappe.throw(_("Filter not allowed: {0}").format(filters[0]), frappe.PermissionError)
				plain_filter_field(filters[1])
			else:
				plain_filter_field(filters[0])
		else:
			for item in filters:
				if not isinstance(item, str):
					plain_filters(item)
	return filters


def plain_order_by(order_by: str | None) -> str | None:
	"""Only plain fields, each with an optional direction, for the same reason."""
	for term in (order_by or "").split(","):
		if order_by and not re.fullmatch(r"\s*\w+(\s+(asc|desc))?\s*", term, re.IGNORECASE):
			frappe.throw(_("Order not allowed: {0}").format(term.strip()), frappe.PermissionError)
	return order_by


def plain_filter_field(field):
	if not re.fullmatch(r"\w+", str(field)):
		frappe.throw(_("Filter not allowed: {0}").format(field), frappe.PermissionError)


@frappe.whitelist(methods=["POST"])
def delete_event(name: str):
	"""Frappe lets only System Managers delete an Event; in the CRM its owner may too."""
	event = frappe.get_doc("Event", name)
	if frappe.has_permission("Event", "delete", doc=event):
		event.delete()
		return
	if event.owner != frappe.session.user:
		frappe.throw(_("Only the event's owner can delete it"), frappe.PermissionError)
	event.delete(ignore_permissions=True)  # its owner, checked above  # nosemgrep: frappe-ignore-permissions


@frappe.whitelist()
def get_event(name: str) -> dict:
	"""An event to look at, under the same rule as get_event_list."""
	Event = frappe.qb.DocType("Event")
	if not visible_events().where(Event.name == name).run():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return add_booking_guests([frappe.get_doc("Event", name).as_dict()])[0]


def add_booking_guests(rows: list[dict]) -> list[dict]:
	"""Mark meetings booked from a booking page with the guest's email: moving or
	deleting one emails them, so the CRM asks first."""
	names = [row.get("name") for row in rows if row.get("name")]
	guests = dict(
		frappe.get_all(
			"CRM Booking",
			filters={"event": ["in", names or [""]], "status": "Confirmed"},
			fields=["event", "guest_email"],
			as_list=True,
		)
	)
	for row in rows:
		row["booking_guest"] = guests.get(row.get("name"))
	return rows


def connected_google_calendar(user: str) -> str | None:
	"""The user's Google Calendar record, if it's enabled, pushes, and has been authorized."""
	if not frappe.db.get_single_value("Google Settings", "enable"):
		return None
	name = frappe.db.get_value(
		"Google Calendar", {"user": user, "enable": 1, "push_to_google_calendar": 1}, "name"
	)
	if name and frappe.get_doc("Google Calendar", name).get_password("refresh_token", raise_exception=False):
		return name


def hold_google_sync(doc, method=None):
	"""Event before_validate: a CRM event asks for sync without picking a calendar, which
	Frappe rejects. Pick the creator's after insert; on later saves, leave it unsynced."""
	if doc.sync_with_google_calendar and not doc.google_calendar and not doc.pulled_from_google_calendar:
		doc.sync_with_google_calendar = 0
		doc.flags.push_to_google = True


def push_to_google(doc, method=None):
	"""Event after_insert: put the event on its creator's Google Calendar, if connected."""
	if not doc.flags.push_to_google:
		return
	calendar = connected_google_calendar(doc.owner)
	if not calendar:
		return
	calendar_id = frappe.db.get_value("Google Calendar", calendar, "google_calendar_id")
	if not calendar_id:
		# Frappe makes the calendar in Google on its first sync and commits mid-request,
		# which would end the savepoint below; the next scheduled sync makes it
		return

	from frappe.integrations.doctype.google_calendar.google_calendar import insert_event_in_google_calendar

	from crm.api.booking import without_messages

	google = {"sync_with_google_calendar": 1, "google_calendar": calendar, "google_calendar_id": calendar_id}
	frappe.db.savepoint("crm_event_google")
	try:
		doc.update(google)
		with without_messages():
			insert_event_in_google_calendar(doc)
		doc.db_set(google, update_modified=False)
	except Exception:
		# a Google error shouldn't stop the event being created; it just won't sync
		frappe.db.rollback(save_point="crm_event_google")
		doc.update({"sync_with_google_calendar": 0, "google_calendar": None, "google_calendar_id": None})
		frappe.log_error(title=f"CRM: Google Calendar sync failed for event {doc.name}")
