import datetime
import json
from zoneinfo import ZoneInfo

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import get_url

from crm.fcrm.doctype.crm_booking_calendar.crm_booking_calendar import (
	UTC,
	from_system_naive,
	to_system_naive,
)

BOOKING_SOURCE = "Booking"
MAX_RANGE_DAYS = 31


def _get_calendar_by_route(route: str, for_update: bool = False):
	name = frappe.db.get_value("CRM Booking Calendar", {"route": route, "enabled": 1})
	if not name:
		frappe.throw(_("Booking calendar not found"), frappe.DoesNotExistError)
	if for_update:
		_lock_calendar(name)
	return frappe.get_doc("CRM Booking Calendar", name)


def _lock_calendar(name: str):
	"""Row-lock the calendar so concurrent bookings on the same page serialize
	and the availability re-check cannot race another insert."""
	frappe.db.get_value("CRM Booking Calendar", name, "name", for_update=True)


def _parse_utc(value: str) -> datetime.datetime:
	try:
		parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
	except (ValueError, AttributeError):
		frappe.throw(_("Invalid datetime: {0}").format(value))
	if parsed.tzinfo is None:
		frappe.throw(_("Datetime must include a timezone offset"))
	return parsed.astimezone(UTC)


def _parse_date(value: str) -> datetime.date:
	try:
		return datetime.date.fromisoformat(value)
	except (ValueError, AttributeError):
		frappe.throw(_("Invalid date: {0}").format(value))


def _price_info(cal) -> dict:
	if not cal.price:
		return {"price": 0, "formatted_price": ""}
	return {
		"price": cal.price,
		"formatted_price": frappe.utils.fmt_money(cal.price, currency=cal.currency or "EUR"),
	}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_calendar(route: str) -> dict:
	"""Public configuration of a booking page."""
	cal = _get_calendar_by_route(route)
	earliest, latest = cal.booking_window_utc()
	return {
		"title": cal.calendar_name,
		"description": cal.description or "",
		"duration": cal.duration,
		"location": cal.location or "",
		"timezone": cal.timezone,
		"min_date": earliest.date().isoformat(),
		"max_date": latest.date().isoformat(),
		**_price_info(cal),
	}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def list_services() -> list[dict]:
	"""Public service menu: every enabled calendar flagged for the directory."""
	rows = frappe.get_all(
		"CRM Booking Calendar",
		filters={"enabled": 1, "show_in_menu": 1},
		fields=["name", "calendar_name", "route", "description", "duration", "location", "price", "currency"],
		order_by="calendar_name asc",
	)
	return [
		{
			"title": row.calendar_name,
			"route": row.route,
			"description": row.description or "",
			"duration": row.duration,
			"location": row.location or "",
			"price": row.price or 0,
			"formatted_price": (
				frappe.utils.fmt_money(row.price, currency=row.currency or "EUR") if row.price else ""
			),
		}
		for row in rows
	]


@frappe.whitelist(allow_guest=True, methods=["GET"])
@rate_limit(limit=120, seconds=60 * 60)
def get_slots(route: str, start_date: str, end_date: str) -> list[str]:
	"""Free slot start times between two dates, as ISO-8601 UTC strings."""
	cal = _get_calendar_by_route(route)
	start, end = _parse_date(start_date), _parse_date(end_date)
	if end < start:
		frappe.throw(_("End date must be on or after start date"))
	if (end - start).days > MAX_RANGE_DAYS:
		frappe.throw(_("Date range too large"))
	return [s["start"].isoformat() for s in cal.get_available_slots(start, end)]


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=10, seconds=60 * 60)
def book(
	route: str,
	start: str,
	invitee_name: str,
	invitee_email: str,
	invitee_phone: str | None = None,
	notes: str | None = None,
	invitee_timezone: str | None = None,
) -> dict:
	"""Create a booking on a free slot; returns the manage token."""
	# row lock on the calendar serializes concurrent bookings for the same page,
	# so the availability re-check below cannot race another insert
	cal = _get_calendar_by_route(route, for_update=True)
	start_utc = _parse_utc(start)
	free_members = cal.is_slot_available(start_utc)
	if not free_members:
		frappe.throw(_("This slot is no longer available. Please pick another one."))

	agent = cal.pick_agent(free_members)
	end_utc = start_utc + datetime.timedelta(minutes=cal.duration)
	tz = _validated_timezone(invitee_timezone) or cal.timezone

	booking = frappe.get_doc(
		{
			"doctype": "CRM Booking",
			"calendar": cal.name,
			"agent": agent,
			"status": "Confirmed",
			"starts_on": to_system_naive(start_utc),
			"ends_on": to_system_naive(end_utc),
			"invitee_name": strip(invitee_name),
			"invitee_email": strip(invitee_email),
			"invitee_phone": strip(invitee_phone),
			"invitee_timezone": tz,
			"notes": strip(notes),
			"amount": cal.price or 0,
			"currency": cal.currency,
		}
	)
	booking.lead = _find_or_create_lead(booking)
	booking.insert(ignore_permissions=True)
	_send_confirmation(cal, booking)
	return _public_booking(cal, booking)


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_booking(token: str) -> dict:
	booking = _get_booking_by_token(token)
	cal = frappe.get_doc("CRM Booking Calendar", booking.calendar)
	return _public_booking(cal, booking)


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=20, seconds=60 * 60)
def cancel_booking(token: str) -> dict:
	booking = _get_booking_by_token(token)
	if booking.status == "Confirmed":
		booking.status = "Cancelled"
		booking.save(ignore_permissions=True)
		_notify_agent(booking, _("Booking cancelled"))
	cal = frappe.get_doc("CRM Booking Calendar", booking.calendar)
	return _public_booking(cal, booking)


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=20, seconds=60 * 60)
def reschedule_booking(token: str, start: str) -> dict:
	booking = _get_booking_by_token(token)
	if booking.status != "Confirmed":
		frappe.throw(_("Only confirmed bookings can be rescheduled"))
	_lock_calendar(booking.calendar)
	cal = frappe.get_doc("CRM Booking Calendar", booking.calendar)
	start_utc = _parse_utc(start)

	# free the current slot while checking the new one; the temporary cancel must
	# not fire "Booking Cancelled" automations
	frappe.flags.in_crm_automation = True
	try:
		booking.status = "Cancelled"
		booking.save(ignore_permissions=True)
		free_members = cal.is_slot_available(start_utc)
		if not free_members:
			booking.status = "Confirmed"
			booking.save(ignore_permissions=True)
			frappe.throw(_("This slot is no longer available. Please pick another one."))
	finally:
		frappe.flags.in_crm_automation = False

	if booking.agent not in free_members:
		booking.agent = cal.pick_agent(free_members)
	booking.status = "Confirmed"
	booking.starts_on = to_system_naive(start_utc)
	booking.ends_on = to_system_naive(start_utc + datetime.timedelta(minutes=cal.duration))
	booking.save(ignore_permissions=True)
	_send_confirmation(cal, booking, rescheduled=True)
	return _public_booking(cal, booking)


# --- helpers ---------------------------------------------------------------


def strip(value: str | None) -> str:
	return (value or "").strip()


def _validated_timezone(tz: str | None) -> str | None:
	if not tz:
		return None
	try:
		ZoneInfo(tz)
	except Exception:
		return None
	return tz


def _get_booking_by_token(token: str):
	if not token or len(token) < 16:
		frappe.throw(_("Invalid booking link"), frappe.PermissionError)
	name = frappe.db.get_value("CRM Booking", {"access_token": token})
	if not name:
		frappe.throw(_("Booking not found"), frappe.DoesNotExistError)
	return frappe.get_doc("CRM Booking", name)


def _public_booking(cal, booking) -> dict:
	return {
		"token": booking.access_token,
		"calendar": cal.calendar_name,
		"route": cal.route,
		"status": booking.status,
		"start": from_system_naive(booking.starts_on).isoformat(),
		"end": from_system_naive(booking.ends_on).isoformat(),
		"duration": cal.duration,
		"location": cal.location or "",
		"invitee_name": booking.invitee_name,
		"invitee_timezone": booking.invitee_timezone or cal.timezone,
		**_price_info(cal),
	}


# --- Google Calendar connection (per user) ---------------------------------


@frappe.whitelist()
def google_calendar_connection() -> dict:
	"""State of the current user's Google Calendar link, for the Connect button."""
	settings_ready = bool(
		frappe.db.get_single_value("Google Settings", "enable")
		and frappe.db.get_single_value("Google Settings", "client_id")
	)
	name = frappe.db.get_value("Google Calendar", {"user": frappe.session.user})
	connected = False
	if name:
		doc = frappe.get_doc("Google Calendar", name)
		try:
			connected = bool(doc.get_password("refresh_token", raise_exception=False))
		except Exception:
			connected = False
	return {"settings_ready": settings_ready, "name": name, "connected": connected}


@frappe.whitelist(methods=["POST"])
def setup_google_calendar() -> dict:
	"""Ensure the current user has a Google Calendar record and return the
	authorize endpoint the browser should visit to run the OAuth flow."""
	state = google_calendar_connection()
	if not state["settings_ready"]:
		frappe.throw(
			_("Google integration is not configured. Set Client ID/Secret in Google Settings first.")
		)
	name = state["name"]
	if not name:
		doc = frappe.get_doc(
			{
				"doctype": "Google Calendar",
				"calendar_name": frappe.utils.get_fullname(frappe.session.user),
				"user": frappe.session.user,
				"enabled": 1,
			}
		)
		doc.insert(ignore_permissions=True)
		name = doc.name
	from urllib.parse import quote

	authorize_url = (
		"/api/method/frappe.integrations.doctype.google_calendar.google_calendar.authorize_access"
		f"?g_calendar={quote(name)}&reauthorize=1"
	)
	return {"name": name, "authorize_url": authorize_url}


def _ensure_booking_source() -> str:
	if not frappe.db.exists("CRM Lead Source", BOOKING_SOURCE):
		frappe.get_doc({"doctype": "CRM Lead Source", "source_name": BOOKING_SOURCE}).insert(
			ignore_permissions=True
		)
	return BOOKING_SOURCE


def _find_or_create_lead(booking) -> str:
	existing = frappe.db.get_value("CRM Lead", {"email": booking.invitee_email, "converted": 0})
	if existing:
		return existing
	from crm.api.form import _default_status

	parts = booking.invitee_name.split(maxsplit=1)
	lead = frappe.get_doc(
		{
			"doctype": "CRM Lead",
			"first_name": parts[0],
			"last_name": parts[1] if len(parts) > 1 else "",
			"email": booking.invitee_email,
			"mobile_no": booking.invitee_phone or "",
			"status": _default_status("CRM Lead"),
			"source": _ensure_booking_source(),
		}
	)
	lead.insert(ignore_permissions=True)
	return lead.name


def _format_when(booking, cal) -> str:
	tz = booking.invitee_timezone or cal.timezone
	local = from_system_naive(booking.starts_on).astimezone(ZoneInfo(tz))
	return f"{local.strftime('%A %d %B %Y, %H:%M')} ({tz})"


def manage_url(cal, booking) -> str:
	return get_url(f"/book/{cal.route}?token={booking.access_token}")


def _send_confirmation(cal, booking, rescheduled: bool = False):
	when = _format_when(booking, cal)
	subject = (_("Rescheduled: {0} — {1}") if rescheduled else _("Confirmed: {0} — {1}")).format(
		cal.calendar_name, when
	)
	location_line = f"<p>{frappe.utils.escape_html(cal.location)}</p>" if cal.location else ""
	if cal.price:
		price = frappe.utils.fmt_money(cal.price, currency=cal.currency or "EUR")
		location_line += f"<p>{_('Price')}: <b>{price}</b></p>"
	message = f"""
		<p>{_("Hi {0},").format(frappe.utils.escape_html(booking.invitee_name))}</p>
		<p>{_("Your booking is confirmed:")}</p>
		<p><b>{frappe.utils.escape_html(cal.calendar_name)}</b><br>{when}</p>
		{location_line}
		<p><a href="{manage_url(cal, booking)}">{_("Reschedule or cancel")}</a></p>
	"""
	frappe.sendmail(
		recipients=[booking.invitee_email],
		subject=subject,
		message=message,
		attachments=[_ics_attachment(cal, booking)],
		reference_doctype="CRM Booking",
		reference_name=booking.name,
	)
	_notify_agent(booking, subject)


def _notify_agent(booking, subject: str):
	agent_email = frappe.db.get_value("User", booking.agent, "email")
	if not agent_email:
		return
	frappe.sendmail(
		recipients=[agent_email],
		subject=f"[{booking.name}] {subject}",
		message=_("{0} ({1}) — status: {2}. Open the CRM for details.").format(
			booking.invitee_name, booking.invitee_email, _(booking.status)
		),
		reference_doctype="CRM Booking",
		reference_name=booking.name,
	)


def _ics_attachment(cal, booking) -> dict:
	fmt = "%Y%m%dT%H%M%SZ"
	start = from_system_naive(booking.starts_on).strftime(fmt)
	end = from_system_naive(booking.ends_on).strftime(fmt)
	stamp = datetime.datetime.now(UTC).strftime(fmt)
	summary = cal.calendar_name.replace(",", r"\,").replace(";", r"\;")
	location = (cal.location or "").replace(",", r"\,").replace(";", r"\;")
	ics = "\r\n".join(
		[
			"BEGIN:VCALENDAR",
			"VERSION:2.0",
			"PRODID:-//CRM//Booking//EN",
			"BEGIN:VEVENT",
			f"UID:{booking.access_token}@crm-booking",
			f"DTSTAMP:{stamp}",
			f"DTSTART:{start}",
			f"DTEND:{end}",
			f"SUMMARY:{summary}",
			f"LOCATION:{location}",
			"END:VEVENT",
			"END:VCALENDAR",
			"",
		]
	)
	return {"fname": "booking.ics", "fcontent": ics}


# --- Settings-modal administration (manager only) --------------------------

MANAGER_ROLES = {"System Manager", "Sales Manager"}


def _check_manager():
	if not MANAGER_ROLES & set(frappe.get_roles()):
		frappe.throw(_("Only sales managers can manage booking calendars"), frappe.PermissionError)


@frappe.whitelist()
def list_calendars_admin() -> list[dict]:
	_check_manager()
	rows = frappe.get_all(
		"CRM Booking Calendar",
		fields=[
			"name",
			"calendar_name",
			"route",
			"enabled",
			"duration",
			"timezone",
			"price",
			"currency",
			"show_in_menu",
		],
		order_by="calendar_name asc",
	)
	upcoming = dict(
		frappe.get_all(
			"CRM Booking",
			filters={"status": "Confirmed", "starts_on": [">=", frappe.utils.now_datetime()]},
			fields=["calendar", "count(name) as total"],
			group_by="calendar",
			as_list=True,
		)
	)
	for row in rows:
		row["upcoming_count"] = upcoming.get(row.name, 0)
	return rows


@frappe.whitelist()
def get_calendar_admin(name: str) -> dict:
	_check_manager()
	cal = frappe.get_doc("CRM Booking Calendar", name)
	return {
		"name": cal.name,
		"calendar_name": cal.calendar_name,
		"route": cal.route,
		"enabled": cal.enabled,
		"description": cal.description or "",
		"location": cal.location or "",
		"timezone": cal.timezone,
		"duration": cal.duration,
		"slot_interval": cal.slot_interval,
		"buffer_before": cal.buffer_before,
		"buffer_after": cal.buffer_after,
		"min_notice_hours": cal.min_notice_hours,
		"max_horizon_days": cal.max_horizon_days,
		"price": cal.price or 0,
		"currency": cal.currency or "EUR",
		"show_in_menu": cal.show_in_menu,
		"check_google_busy": cal.check_google_busy,
		"members": [m.user for m in cal.members],
		"availability": [
			{"workday": a.workday, "start_time": str(a.start_time), "end_time": str(a.end_time)}
			for a in cal.availability
		],
	}


@frappe.whitelist(methods=["POST"])
def save_calendar(calendar: dict | str, name: str | None = None) -> dict:
	_check_manager()
	if isinstance(calendar, str):
		calendar = json.loads(calendar)

	values = {
		"calendar_name": (calendar.get("calendar_name") or "").strip(),
		"route": calendar.get("route") or "",
		"enabled": 1 if calendar.get("enabled") else 0,
		"description": calendar.get("description") or "",
		"location": calendar.get("location") or "",
		"timezone": calendar.get("timezone") or "Europe/Rome",
		"duration": int(calendar.get("duration") or 30),
		"slot_interval": int(calendar.get("slot_interval") or 0),
		"buffer_before": int(calendar.get("buffer_before") or 0),
		"buffer_after": int(calendar.get("buffer_after") or 0),
		"min_notice_hours": int(calendar.get("min_notice_hours") or 0),
		"max_horizon_days": int(calendar.get("max_horizon_days") or 30),
		"price": float(calendar.get("price") or 0),
		"currency": calendar.get("currency") or "EUR",
		"show_in_menu": 1 if calendar.get("show_in_menu") else 0,
		"check_google_busy": 1 if calendar.get("check_google_busy") else 0,
		"members": [{"user": u} for u in calendar.get("members") or []],
		"availability": [
			{
				"workday": a.get("workday"),
				"start_time": a.get("start_time"),
				"end_time": a.get("end_time"),
			}
			for a in calendar.get("availability") or []
		],
	}
	if not values["calendar_name"]:
		frappe.throw(_("Calendar name is required"))

	if name:
		doc = frappe.get_doc("CRM Booking Calendar", name)
		doc.update(values)
		doc.save()
	else:
		doc = frappe.get_doc({"doctype": "CRM Booking Calendar", **values})
		doc.insert()
	return get_calendar_admin(doc.name)


@frappe.whitelist(methods=["POST"])
def delete_calendar(name: str) -> None:
	_check_manager()
	frappe.delete_doc("CRM Booking Calendar", name)
