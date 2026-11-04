# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Public appointment booking.

A CRM Booking Page holds a host's (or a team's) weekly hours. Visitors on
/crm-book/<route> see the open slots, which are those hours minus each host's
busy time from CRM Events and, when connected, their Google Calendar. A booking
creates an Event owned by the host and links it to the visitor's lead or deal,
creating a lead when none exists.

Times cross the API as UTC ISO strings. Frappe stores datetimes naive in the
system timezone, so everything is converted at the edges.
"""

import re
import secrets
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import frappe
from frappe import _
from frappe.query_builder.functions import Max
from frappe.rate_limiter import rate_limit
from frappe.utils import cint, get_datetime, get_system_timezone, get_time, get_url, validate_email_address


class SlotUnavailableError(frappe.ValidationError):
	"""The visitor's time went to someone else; the page sends them back to pick again."""

	http_status_code = 409


WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
# a visitor browses a month at a time; anything wider is not a calendar view
MAX_RANGE = timedelta(days=42)
GOOGLE_BUSY_CACHE_SECONDS = 5 * 60
# CRM Booking Page.guest_reminder
REMINDER_OFFSETS = {"1 hour before": timedelta(hours=1), "1 day before": timedelta(days=1)}
# who the visitor is; left out of the answers shown in the meeting and emails
CONTACT_FIELDS = {"first_name", "last_name", "lead_name", "email", "mobile_no", "phone"}
# limits that keep a public page from being used to flood a calendar or someone's inbox
MAX_UPCOMING_PER_EMAIL = 2  # per page
MAX_BOOKINGS_PER_EMAIL_PER_DAY = 5  # across all pages
MAX_BOOKINGS_PER_PAGE_PER_HOUR = 30
HOST_LOCK_SECONDS = 30


# Public page: free slots of a live page, rate limited
@frappe.whitelist(allow_guest=True)  # nosemgrep: guest-whitelisted-method
@rate_limit(limit=300, seconds=60 * 60)
def get_slots(route: str, start: str, end: str, token: str | None = None) -> list[str]:
	"""Open slot start times between `start` and `end`, as UTC ISO strings.

	With a booking `token` the slots are the booking host's, for rescheduling."""
	page = get_page(route)
	start_utc, end_utc = parse_utc(start), parse_utc(end)
	if end_utc <= start_utc or end_utc - start_utc > MAX_RANGE:
		frappe.throw(_("Pick a range of up to six weeks"))
	booking = get_booking_by_token(token) if token else None
	hosts = [booking.host] if booking else page_hosts(page)
	return [to_iso(s) for s in available_slots(page, start_utc, end_utc, hosts, booking)]


# Public page: visitors book without an account, rate limited
@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
@rate_limit(limit=10, seconds=60 * 60)
def book(
	route: str,
	start: str,
	values: dict | str | None = None,
	timezone: str | None = None,
) -> dict:
	"""Book `start` with the answers to the page's form, which include name and email."""
	page = get_page(route)
	doc_values, answers = clean_form_values(page, frappe.parse_json(values) or {})
	email = str(doc_values.get("email") or "").lower()
	if not validate_email_address(email):
		frappe.throw(_("Please enter a valid email address"))
	doc_values["email"] = email
	check_booking_limits(page, email)
	full_name = (
		" ".join(str(doc_values.get(f) or "") for f in ("first_name", "last_name")).strip()
		or email.split("@")[0]
	)[:140]
	phone = doc_values.get("mobile_no") or doc_values.get("phone")

	start_utc = parse_utc(start)
	end_utc = start_utc + timedelta(minutes=page.duration)
	hosts = page_hosts(page)
	lock_hosts(hosts)
	free_hosts = available_slots(page, start_utc, end_utc, hosts).get(start_utc)
	if not free_hosts:
		frappe.throw(_("That time was just taken. Please pick another one."), exc=SlotUnavailableError)
	host = pick_host(page, free_hosts)

	frappe.flags.in_crm_booking = True
	try:
		reference = link_record(page, email, host, doc_values)
	finally:
		frappe.flags.in_crm_booking = False
	guest = {"guest_name": full_name, "guest_email": email, "guest_phone": phone}
	booking = make_booking(page, host, start_utc, guest, reference, answers, timezone, doc_values)
	return public_booking(booking, page, frappe.get_doc("Event", booking.event))


def make_booking(page, host, start_utc, guest, reference, answers=None, timezone=None, values=None):
	"""The booking and its meeting, with the emails and the host's notification."""
	booking = frappe.get_doc(
		{
			"doctype": "CRM Booking",
			"booking_page": page.name,
			"host": host,
			"starts_on": to_system(start_utc),
			"ends_on": to_system(start_utc + timedelta(minutes=page.duration)),
			"guest_timezone": valid_timezone(timezone),
			**guest,
			"answers": answers or {},
			"reference_doctype": reference[0],
			"reference_docname": reference[1],
			"token": secrets.token_urlsafe(24),
		}
	).insert(ignore_permissions=True)

	event = create_event(page, booking, values)
	booking.db_set("event", event.name, update_modified=False)
	send_booking_emails(page, booking, event, "confirmed")
	notify_host(page, booking, "confirmed")
	return booking


# Guest's own booking, found only by its secret token
@frappe.whitelist(allow_guest=True)  # nosemgrep: guest-whitelisted-method
def get_booking(token: str) -> dict:
	booking = get_booking_by_token(token, confirmed_only=False)
	page = frappe.get_doc("CRM Booking Page", booking.booking_page)
	event = frappe.get_doc("Event", booking.event) if booking.event else None
	return public_booking(booking, page, event)


# Guest's own booking, found only by its secret token, rate limited
@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
@rate_limit(limit=20, seconds=60 * 60)
def cancel_booking(token: str, reason: str | None = None) -> dict:
	booking = get_booking_by_token(token)
	ensure_upcoming(booking)
	booking.status = "Cancelled"
	booking.cancel_reason = (reason or "").strip()[:500]
	booking.save(ignore_permissions=True)

	page = frappe.get_doc("CRM Booking Page", booking.booking_page)
	event = None
	if booking.event and frappe.db.exists("Event", booking.event):
		event = frappe.get_doc("Event", booking.event)
		event.status = "Cancelled"
		event.flags.from_crm_booking = True
		event.save(ignore_permissions=True)
		cancel_google_event(event)
	send_booking_emails(page, booking, event, "cancelled")
	notify_host(page, booking, "cancelled")
	return public_booking(booking, page, event)


# Guest's own booking, found only by its secret token, rate limited
@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
@rate_limit(limit=20, seconds=60 * 60)
def reschedule_booking(token: str, start: str) -> dict:
	booking = get_booking_by_token(token)
	ensure_upcoming(booking)
	page = get_page(frappe.db.get_value("CRM Booking Page", booking.booking_page, "route"))

	start_utc = parse_utc(start)
	end_utc = start_utc + timedelta(minutes=page.duration)
	lock_hosts([booking.host])
	if not available_slots(page, start_utc, end_utc, [booking.host], booking).get(start_utc):
		frappe.throw(_("That time was just taken. Please pick another one."), exc=SlotUnavailableError)

	booking.starts_on = to_system(start_utc)
	booking.ends_on = to_system(end_utc)
	booking.save(ignore_permissions=True)

	event = None
	if booking.event and frappe.db.exists("Event", booking.event):
		event = frappe.get_doc("Event", booking.event)
		event.starts_on = booking.starts_on
		event.ends_on = booking.ends_on
		event.flags.from_crm_booking = True
		# saving pushes the new time to Google, which emails the attendees
		event.save(ignore_permissions=True)
	send_booking_emails(page, booking, event, "rescheduled")
	notify_host(page, booking, "rescheduled")
	return public_booking(booking, page, event)


# Managing pages


@frappe.whitelist()
def list_pages() -> list[dict]:
	pages = frappe.get_list(
		"CRM Booking Page",
		fields=["name", "title", "route", "enabled", "duration", "location_type", "document_type"],
		order_by="creation desc",
	)
	hosts = frappe.get_all(
		"CRM Booking Page Host",
		filters={"parenttype": "CRM Booking Page", "parent": ["in", [p.name for p in pages] or [""]]},
		fields=["parent", "user"],
		order_by="idx",
	)
	counts = dict(
		frappe.get_all(
			"CRM Booking",
			filters={"booking_page": ["in", [p.name for p in pages] or [""]]},
			fields=["booking_page", {"COUNT": "*", "as": "count"}],
			group_by="booking_page",
			as_list=True,
		)
	)
	for page in pages:
		page.hosts = [h.user for h in hosts if h.parent == page.name]
		page.bookings = counts.get(page.name, 0)
	return pages


@frappe.whitelist()
def create_page(title: str, route: str, document_type: str = "CRM Lead") -> str:
	"""A new page hosted by the current user, open 9 to 5 on weekdays, whose bookings
	create a lead or a deal."""
	user_tz = frappe.db.get_value("User", frappe.session.user, "time_zone")
	page = frappe.get_doc(
		{
			"doctype": "CRM Booking Page",
			"title": title,
			"route": route,
			"enabled": 0,
			"document_type": document_type,
			"timezone": valid_timezone(user_tz) or get_system_timezone(),
			"hosts": [{"user": frappe.session.user}],
			"availability": [
				{"workday": day, "start_time": "09:00:00", "end_time": "17:00:00"} for day in WEEKDAYS[:5]
			],
		}
	).insert()
	return page.name


# Pages and bookings


def get_page(route: str):
	"""An enabled page by route. People who can edit pages may also open disabled ones, to preview."""
	filters = {"route": route}
	if not (frappe.session.user != "Guest" and frappe.has_permission("CRM Booking Page", "write")):
		filters["enabled"] = 1
	name = frappe.db.get_value("CRM Booking Page", filters)
	if not name:
		raise frappe.DoesNotExistError(_("This booking page does not exist"))
	return frappe.get_doc("CRM Booking Page", name)


def page_hosts(page) -> list[str]:
	users = [h.user for h in page.hosts]
	enabled = set(frappe.get_all("User", filters={"name": ["in", users], "enabled": 1}, pluck="name"))
	return [u for u in users if u in enabled]


def public_page(page) -> dict:
	"""What a visitor may see of a page."""
	hosts = page_hosts(page)
	return {
		"title": page.title,
		"route": page.route,
		"description": page.description or "",
		"duration": page.duration,
		"location_type": page.location_type,
		"location": page.location if page.location_type == "In person" else "",
		"timezone": page_timezone(page),
		"max_days_ahead": cint(page.max_days_ahead) or 30,
		"hosts": [
			{"full_name": u.full_name, "image": u.user_image}
			for u in frappe.get_all(
				"User", filters={"name": ["in", hosts]}, fields=["full_name", "user_image"]
			)
		],
		"confirmation_message": page.confirmation_message or "",
	}


def public_booking(booking, page, event=None) -> dict:
	return {
		"token": booking.token,
		"status": booking.status,
		"start": to_iso(to_utc(booking.starts_on)),
		"end": to_iso(to_utc(booking.ends_on)),
		"guest_name": booking.guest_name,
		"guest_email": booking.guest_email,
		"host": frappe.db.get_value("User", booking.host, "full_name"),
		"meeting_link": meeting_link(page, event),
		"page": {"title": page.title, "route": page.route, "duration": page.duration},
		"upcoming": to_utc(booking.starts_on) > datetime.now(UTC),
	}


def get_booking_by_token(token: str | None, confirmed_only: bool = True):
	name = token and frappe.db.get_value("CRM Booking", {"token": token})
	if not name:
		raise frappe.DoesNotExistError(_("This booking does not exist"))
	booking = frappe.get_doc("CRM Booking", name)
	if confirmed_only and booking.status != "Confirmed":
		frappe.throw(_("This booking was cancelled"))
	return booking


def ensure_upcoming(booking):
	if to_utc(booking.starts_on) <= datetime.now(UTC):
		frappe.throw(_("This meeting has already started"))


def check_booking_limits(page, email: str):
	"""Stop one address or one page from filling calendars and sending mail in bulk."""
	now = datetime.now(UTC)
	upcoming = frappe.db.count(
		"CRM Booking",
		{
			"booking_page": page.name,
			"guest_email": email,
			"status": "Confirmed",
			"starts_on": [">", to_system(now)],
		},
	)
	if upcoming >= MAX_UPCOMING_PER_EMAIL:
		frappe.throw(_("You already have a meeting booked. Use the link in your email to change it."))
	day_ago = to_system(now - timedelta(days=1))
	if (
		frappe.db.count("CRM Booking", {"guest_email": email, "creation": [">", day_ago]})
		>= MAX_BOOKINGS_PER_EMAIL_PER_DAY
	):
		frappe.throw(_("Too many bookings from this email address today"), frappe.RateLimitExceededError)
	hour_ago = to_system(now - timedelta(hours=1))
	if (
		frappe.db.count("CRM Booking", {"booking_page": page.name, "creation": [">", hour_ago]})
		>= MAX_BOOKINGS_PER_PAGE_PER_HOUR
	):
		frappe.throw(
			_("This page is getting a lot of bookings. Please try again later."),
			frappe.RateLimitExceededError,
		)


def booking_form(page):
	"""The page's own CRM web form."""
	if not page.web_form:
		return None
	form = frappe.get_doc("Web Form", page.web_form)
	return form if form.doc_type in ("CRM Lead", "CRM Deal") else None


def clean_form_values(page, values: dict) -> tuple[dict, dict]:
	"""The visitor's answers to the page's form, as field values for the lead or deal,
	and as label → answer (name and contact details left out) for the meeting
	description and emails.

	Only the form's own fields are taken, and only those the form shows for these
	answers. Required fields, including "required if" ones, are enforced here with
	the same conditions the page evaluates."""
	from crm.utils.form_conditions import check_form_values, field_visible

	form = booking_form(page)
	if not form:
		return {}, {}
	fields = [f for f in form.web_form_fields if f.fieldtype not in ("Section Break", "Column Break")]
	answered = {}
	for f in fields:
		value = values.get(f.fieldname)
		answered[f.fieldname] = cint(value) if f.fieldtype == "Check" else str(value or "").strip()[:2000]
	check_form_values(fields, answered)

	doc_values, answers = {}, {}
	for f in fields:
		value = answered[f.fieldname]
		if not value or not field_visible(f, answered):
			continue
		if f.fieldtype == "Select" and value not in (f.options or "").split("\n"):
			frappe.throw(_("Please pick an option for: {0}").format(f.label or f.fieldname))
		if f.fieldtype == "Link" and value not in link_values(f.options):
			frappe.throw(_("Please pick an option for: {0}").format(f.label or f.fieldname))
		doc_values[f.fieldname] = value
		if f.fieldname not in CONTACT_FIELDS:
			answers[f.label or f.fieldname] = _("Yes") if f.fieldtype == "Check" else value
	return doc_values, answers


def link_values(doctype: str | None) -> set[str]:
	"""The records a visitor can pick in a Link field, as the form shows them."""
	from crm.www.crm_form import _link_field_options

	return {o["value"] for o in _link_field_options(doctype)} if doctype else set()


def lock_hosts(hosts: list[str]):
	"""Serialise bookings per host so two visitors can't take the same slot.

	A named lock in Redis, held until the booking commits or rolls back, so the
	free/busy checks and Google calls inside it don't hold database row locks.
	A transaction that already holds a host's lock carries on with it."""
	held = held_host_locks()
	locks = []
	for host in sorted(set(hosts) - set(held)):
		lock = frappe.cache.lock(
			frappe.cache.make_key(f"crm_booking_host:{host}"),
			timeout=HOST_LOCK_SECONDS,
			blocking_timeout=HOST_LOCK_SECONDS,
		)
		if not lock.acquire():
			release_locks(locks)
			frappe.throw(_("That time was just taken. Please pick another one."), exc=SlotUnavailableError)
		locks.append(lock)
		held[host] = lock
	if locks:
		frappe.db.after_commit.add(lambda: release_locks(locks))
		frappe.db.after_rollback.add(lambda: release_locks(locks))


def held_host_locks() -> dict:
	"""Host → lock this request holds until its transaction ends."""
	if not hasattr(frappe.local, "crm_booking_host_locks"):
		frappe.local.crm_booking_host_locks = {}
	return frappe.local.crm_booking_host_locks


def release_locks(locks):
	from redis.exceptions import LockError

	held = held_host_locks()
	for host, lock in list(held.items()):
		if lock in locks:
			del held[host]
	for lock in locks:
		try:
			lock.release()
		except LockError:
			pass  # expired, or already released by the other of commit/rollback
	locks.clear()


def pick_host(page, free_hosts: list[str]) -> str:
	"""Round robin: the free host who was booked from this page longest ago."""
	if len(free_hosts) == 1:
		return free_hosts[0]
	Booking = frappe.qb.DocType("CRM Booking")
	rows = (
		frappe.qb.from_(Booking)
		.select(Booking.host, Max(Booking.creation).as_("last"))
		.where((Booking.booking_page == page.name) & Booking.host.isin(free_hosts))
		.groupby(Booking.host)
		.run(as_dict=True)
	)
	last_booked = {row.host: row.last for row in rows}
	order = {h.user: h.idx for h in page.hosts}
	return min(free_hosts, key=lambda h: (last_booked.get(h) or datetime.min, order.get(h, 0)))


def link_record(page, email, host, values) -> tuple[str | None, str | None]:
	"""The visitor's open lead or deal, or a new one of the page's type for the host.

	An existing record is only linked, never changed: anyone can type any email, so the
	answers stay on the booking. A new record gets them all, plus the form's hidden
	defaults, as if it came in through the form."""
	doctype = page.document_type or "CRM Lead"
	lead = frappe.db.get_value("CRM Lead", {"email": email, "converted": 0}, "name", order_by="modified desc")
	contact = frappe.db.get_value("Contact Email", {"email_id": email, "parenttype": "Contact"}, "parent")
	deal = contact and frappe.db.get_value(
		"CRM Contacts", {"contact": contact, "parenttype": "CRM Deal"}, "parent", order_by="modified desc"
	)
	# prefer a record of the page's own type, so answers land on the right fields
	for found_doctype, found in sorted(
		(("CRM Lead", lead), ("CRM Deal", deal)), key=lambda r: r[0] != doctype
	):
		if found:
			return found_doctype, found

	if not page.create_lead:
		return None, None

	owner_field = "lead_owner" if doctype == "CRM Lead" else "deal_owner"
	doc = frappe.get_doc({**values, "doctype": doctype, owner_field: host, "source": page.lead_source})
	# crm.api.form.enrich_form_submission applies the form's hidden defaults, source,
	# and for deals the contact and organization, on these flags, as for a form submission
	flags = frappe.flags.in_web_form, frappe.form_dict.get("web_form")
	frappe.flags.in_web_form = True
	frappe.form_dict.web_form = page.web_form
	try:
		doc.insert(ignore_permissions=True)
	finally:
		frappe.flags.in_web_form, frappe.form_dict.web_form = flags
	return doctype, doc.name


# Slots


def available_slots(page, start_utc, end_utc, hosts, booking=None) -> dict[datetime, list[str]]:
	"""Slot start → hosts free for it, for slots starting in [start_utc, end_utc).

	`booking` is one being rescheduled; its own meeting doesn't count as busy."""
	now = datetime.now(UTC)
	start_utc = max(start_utc, now + timedelta(hours=cint(page.min_notice)))
	end_utc = min(end_utc, now + timedelta(days=cint(page.max_days_ahead) or 30))
	if start_utc >= end_utc or not hosts:
		return {}
	slots = list(candidate_slots(page, start_utc, end_utc))
	if not slots:
		return {}

	duration = timedelta(minutes=page.duration)
	buffer = timedelta(minutes=cint(page.buffer))
	busy = {h: busy_times(h, slots[0] - buffer, slots[-1] + duration + buffer, booking) for h in hosts}

	out = {}
	for slot in slots:
		before, after = slot - buffer, slot + duration + buffer
		free = [h for h in hosts if not any(b_start < after and b_end > before for b_start, b_end in busy[h])]
		if free:
			out[slot] = free
	return out


def candidate_slots(page, start_utc, end_utc):
	"""Slot starts from the page's weekly hours, minus holidays, in [start_utc, end_utc)."""
	tz = ZoneInfo(page_timezone(page))
	duration = timedelta(minutes=page.duration)
	step = timedelta(minutes=cint(page.slot_interval) or page.duration)
	holidays = holiday_dates(page)
	hours = {}
	for row in page.availability:
		hours.setdefault(row.workday, []).append((get_time(row.start_time), get_time(row.end_time)))

	day = start_utc.astimezone(tz).date()
	last_day = end_utc.astimezone(tz).date()
	while day <= last_day:
		if day not in holidays:
			for open_at, close_at in hours.get(WEEKDAYS[day.weekday()], []):
				slot = datetime.combine(day, open_at, tzinfo=tz)
				close = datetime.combine(day, close_at, tzinfo=tz)
				while slot + duration <= close:
					slot_utc = slot.astimezone(UTC)
					if start_utc <= slot_utc < end_utc:
						yield slot_utc
					slot += step
		day += timedelta(days=1)


def holiday_dates(page) -> set:
	if not page.holiday_list:
		return set()
	return set(
		frappe.get_all(
			"CRM Holiday",
			filters={"parent": page.holiday_list, "parenttype": "CRM Holiday List"},
			pluck="date",
		)
	)


def busy_times(host, start_utc, end_utc, booking=None) -> list[tuple[datetime, datetime]]:
	"""The host's busy intervals (UTC) overlapping [start_utc, end_utc)."""
	busy = event_busy_times(host, start_utc, end_utc, booking and booking.event)
	google = google_busy_times(host, start_utc, end_utc)
	if booking:
		# the booking's own event as pulled back from Google
		own = (to_utc(booking.starts_on), to_utc(booking.ends_on))
		google = [b for b in google if b != own]
	return busy + google


def event_busy_times(host, start_utc, end_utc, exclude_event=None) -> list[tuple[datetime, datetime]]:
	"""Open, timed CRM Events the host owns or attends. All-day events don't block time."""
	emails = {host, frappe.db.get_value("User", host, "email")} - {None}
	start, end = to_system(start_utc), to_system(end_utc)
	events = frappe.db.sql(
		"""
		select distinct e.name, e.starts_on, e.ends_on, e.repeat_this_event, e.repeat_on, e.repeat_till,
			e.monday, e.tuesday, e.wednesday, e.thursday, e.friday, e.saturday, e.sunday
		from `tabEvent` e
		left join `tabEvent Participants` p on p.parent = e.name and p.parenttype = 'Event'
		where e.status = 'Open' and e.all_day = 0 and e.name != %(exclude)s
			and (e.owner = %(host)s or p.email in %(emails)s)
			and e.starts_on < %(end)s
			and (
				coalesce(e.ends_on, e.starts_on) > %(start)s
				or (e.repeat_this_event = 1 and coalesce(e.repeat_till, '3000-01-01') >= date(%(start)s))
			)
		""",
		{"host": host, "emails": tuple(emails), "start": start, "end": end, "exclude": exclude_event or ""},
		as_dict=True,
	)
	busy = []
	for e in events:
		for occ_start, occ_end in occurrences(e, start, end):
			busy.append((to_utc(occ_start), to_utc(occ_end)))
	return busy


def occurrences(event, start, end):
	"""(start, end) of each occurrence of a possibly repeating event within [start, end)."""
	length = (event.ends_on - event.starts_on) if event.ends_on else timedelta(0)
	if not event.repeat_this_event:
		yield event.starts_on, event.starts_on + length
		return

	first = event.starts_on.date()
	day = max(first, (start - length).date())
	last = end.date()
	if event.repeat_till:
		last = min(last, event.repeat_till)
	weekdays = [WEEKDAYS[i].lower() for i in range(7)]
	any_weekday = any(event.get(d) for d in weekdays)
	while day <= last:
		months = (day.year - first.year) * 12 + day.month - first.month
		repeats = {
			"Daily": True,
			"Weekly": event.get(weekdays[day.weekday()]) if any_weekday else day.weekday() == first.weekday(),
			"Monthly": day.day == first.day,
			"Quarterly": day.day == first.day and months % 3 == 0,
			"Half Yearly": day.day == first.day and months % 6 == 0,
			"Yearly": day.day == first.day and day.month == first.month,
		}.get(event.repeat_on)
		if repeats:
			occ_start = datetime.combine(day, event.starts_on.time())
			yield occ_start, occ_start + length
		day += timedelta(days=1)


def google_busy_times(host, start_utc, end_utc) -> list[tuple[datetime, datetime]]:
	"""Busy blocks from the host's Google Calendar, when they've connected one.

	Cached per UTC day, so however a visitor slices the range, Google is asked about
	each day at most once every few minutes."""
	calendar = frappe.db.get_value("Google Calendar", {"user": host, "enable": 1}, "name")
	if not calendar:
		return []
	first = start_utc.replace(hour=0, minute=0, second=0, microsecond=0)
	days = [first + timedelta(days=i) for i in range((end_utc - first).days + 1)]

	def key(day):
		return f"crm_booking_google_busy:{calendar}:{day.date()}"

	cached = {day: frappe.cache.get_value(key(day)) for day in days}
	missing = [day for day, blocks in cached.items() if blocks is None]
	if missing:
		fetched = fetch_google_busy(calendar, missing[0], missing[-1] + timedelta(days=1))
		for day in missing:
			# a block spanning midnight is kept on every day it touches
			cached[day] = [
				(s, e) for s, e in fetched if parse_utc(s) < day + timedelta(days=1) and parse_utc(e) > day
			]
			frappe.cache.set_value(key(day), cached[day], expires_in_sec=GOOGLE_BUSY_CACHE_SECONDS)
	blocks = {block for day in days for block in cached[day]}
	return [(parse_utc(s), parse_utc(e)) for s, e in blocks]


def fetch_google_busy(calendar, start_utc, end_utc) -> list[tuple[str, str]]:
	from frappe.integrations.doctype.google_calendar.google_calendar import get_google_calendar_object

	try:
		service, account = get_google_calendar_object(calendar)
		# the host's own meetings live in "primary"; Frappe may sync into a calendar of its own
		ids = {"primary", account.google_calendar_id} - {None, ""}
		result = (
			service.freebusy()
			.query(
				body={
					"timeMin": to_iso(start_utc),
					"timeMax": to_iso(end_utc),
					"items": [{"id": i} for i in ids],
				}
			)
			.execute()
		)
	except Exception:
		frappe.log_error(title=f"CRM Booking: Google free/busy failed for {calendar}")
		return []
	return [
		(b["start"], b["end"]) for cal in result.get("calendars", {}).values() for b in cal.get("busy", [])
	]


# Events and emails


def event_title(page, booking, values: dict | None = None) -> str:
	"""The page's meeting title with its placeholders filled in; unknown ones are left as typed."""
	fields = {
		**{k: plain(v) for k, v in (values or {}).items()},
		"guest": plain(booking.guest_name),
		"host": frappe.db.get_value("User", booking.host, "full_name") or booking.host,
		"page": page.title,
	}
	template = (page.event_title or "").strip()
	if not template:
		return _("{0} ({1})").format(page.title, plain(booking.guest_name))
	return re.sub(r"\{(\w+)\}", lambda m: fields.get(m.group(1), m.group(0)), template)[:140]


def plain(value) -> str:
	"""A visitor's text as it may appear in a meeting title, which Google sends out from
	the host's account: one short line, no links."""
	text = re.sub(r"\s+", " ", str(value or "")).strip()
	text = re.sub(r"(?i)\b(?:https?://|www\.)\S*", "", text)
	text = re.sub(r"(?i)\b[\w-]+(?:\.[\w-]+)*\.[a-z]{2,}(?:/\S*)?", "", text)
	return re.sub(r"\s+", " ", text).strip()[:60]


def create_event(page, booking, values: dict | None = None):
	def build():
		event = frappe.new_doc("Event")
		event.update(
			{
				"subject": event_title(page, booking, values),
				"event_category": "Meeting",
				"event_type": "Private",
				"starts_on": booking.starts_on,
				"ends_on": booking.ends_on,
				"description": event_description(booking),
				"location": page.location if page.location_type in ("In person", "Custom link") else "",
			}
		)
		if booking.reference_doctype:
			event.reference_doctype = booking.reference_doctype
			event.reference_docname = booking.reference_docname
			event.append(
				"event_participants",
				{
					"reference_doctype": booking.reference_doctype,
					"reference_docname": booking.reference_docname,
					"email": booking.guest_email,
				},
			)
		return event

	event = build()
	calendar = frappe.db.get_value(
		"Google Calendar", {"user": booking.host, "enable": 1, "push_to_google_calendar": 1}, "name"
	)
	if calendar:
		event.sync_with_google_calendar = 1
		event.google_calendar = calendar
		event.add_video_conferencing = int(page.location_type == "Google Meet")
		frappe.db.savepoint("crm_booking_event")
		try:
			event.insert(ignore_permissions=True)
		except Exception:
			# keep the booking even if Google is unreachable; it just won't sync
			frappe.db.rollback(save_point="crm_booking_event")
			frappe.log_error(title=f"CRM Booking: Google sync failed for {booking.name}")
			event = build()
			event.insert(ignore_permissions=True)
	else:
		event.insert(ignore_permissions=True)

	# insert always stamps the session user (Guest) as owner; the host owns the meeting
	event.db_set("owner", booking.host, update_modified=False)
	event.reload()
	return event


def event_description(booking) -> str:
	"""Who booked, then their answers, one per line."""
	esc = frappe.utils.escape_html
	contact = " · ".join(esc(v) for v in (booking.guest_name, booking.guest_email, booking.guest_phone) if v)
	lines = [f"<p>{contact}</p>"]
	answers = frappe.parse_json(booking.answers) or {}
	if answers:
		lines.append("<p>" + "<br>".join(f"{esc(q)}: {esc(a)}" for q, a in answers.items()) + "</p>")
	return "".join(lines)


def cancel_google_event(event):
	if not (event.sync_with_google_calendar and event.google_calendar_event_id):
		return
	from frappe.integrations.doctype.google_calendar.google_calendar import delete_event_from_google_calendar

	try:
		delete_event_from_google_calendar(event)
	except Exception:
		frappe.log_error(title=f"CRM Booking: Google cancel failed for {event.name}")


def meeting_link(page, event) -> str:
	if page.location_type == "Google Meet":
		return (event and event.google_meet_link) or ""
	if page.location_type == "Custom link":
		return page.location or ""
	return ""


def sync_booking_from_event(event, method=None):
	"""Keep a booking in step with its meeting when the host cancels, deletes or moves
	it in the CRM: the visitor's booking page and emails then match the calendar."""
	if event.flags.from_crm_booking or event.is_new():
		return
	name = frappe.db.get_value("CRM Booking", {"event": event.name, "status": "Confirmed"})
	if not name:
		return
	booking = frappe.get_doc("CRM Booking", name)
	page = frappe.get_doc("CRM Booking Page", booking.booking_page)

	if method == "on_trash" or event.status == "Cancelled":
		booking.status = "Cancelled"
		booking.cancel_reason = _("Cancelled by {0}").format(
			frappe.db.get_value("User", booking.host, "full_name")
		)
		if method == "on_trash":
			# the meeting is going; keep the booking as a record without it
			booking.event = None
		booking.save(ignore_permissions=True)
		send_booking_emails(page, booking, None, "cancelled", to_host=False)
		return

	starts_on, ends_on = get_datetime(event.starts_on), get_datetime(event.ends_on or event.starts_on)
	if (starts_on, ends_on) != (get_datetime(booking.starts_on), get_datetime(booking.ends_on)):
		booking.starts_on, booking.ends_on = starts_on, ends_on
		booking.save(ignore_permissions=True)
		send_booking_emails(page, booking, event, "rescheduled", to_host=False)


def send_booking_emails(page, booking, event, action: str, to_host: bool = True):
	"""Tell the guest and the host a booking was confirmed, rescheduled or cancelled.

	`to_host` is off when the host made the change themselves."""
	manage_url = get_url(f"/crm-book/{page.route}?booking={booking.token}")
	link = meeting_link(page, event)
	invited_by_google = bool(event and event.google_calendar_event_id and booking.reference_doctype)
	subjects = {
		"confirmed": _("Confirmed: {0}"),
		"rescheduled": _("Rescheduled: {0}"),
		"cancelled": _("Cancelled: {0}"),
		"reminder": _("Reminder: {0}"),
	}
	host_name, host_email, host_tz = frappe.db.get_value(
		"User", booking.host, ["full_name", "email", "time_zone"]
	)

	guest_when = format_when(booking, booking.guest_timezone or page_timezone(page))
	attachments = []
	if action in ("confirmed", "rescheduled") and not invited_by_google:
		attachments.append(
			{"fname": "invite.ics", "fcontent": ics(page, booking, host_name, host_email, link)}
		)
	frappe.sendmail(
		recipients=[booking.guest_email],
		reply_to=host_email,
		subject=subjects[action].format(page.title) + f" · {guest_when}",
		template="crm_booking",
		# Frappe's card layout, with the business's own brand
		with_container=True,
		wrapper="crm/templates/emails/crm_booking_wrapper.html",
		args={
			"action": action,
			"title": page.title,
			"when": guest_when,
			"with_name": host_name,
			"location": location_text(page, link),
			"link": link,
			"manage_url": manage_url if action != "cancelled" else "",
			"message": page.confirmation_message if action == "confirmed" else "",
			"reason": booking.cancel_reason if action == "cancelled" else "",
		},
		attachments=attachments,
		reference_doctype="CRM Booking",
		reference_name=booking.name,
	)

	if not to_host:
		return
	host_when = format_when(booking, host_tz or get_system_timezone())
	record_url = ""
	if booking.reference_doctype:
		route = "leads" if booking.reference_doctype == "CRM Lead" else "deals"
		record_url = get_url(f"/crm/{route}/{booking.reference_docname}")
	frappe.sendmail(
		recipients=[host_email],
		reply_to=booking.guest_email,
		subject=subjects[action].format(f"{page.title} with {booking.guest_name}") + f" · {host_when}",
		template="crm_booking",
		# Frappe's card layout, with the business's own brand
		with_container=True,
		wrapper="crm/templates/emails/crm_booking_wrapper.html",
		args={
			"action": action,
			"title": page.title,
			"when": host_when,
			"with_name": f"{booking.guest_name} ({booking.guest_email})",
			"guest": booking.guest_name,
			"location": location_text(page, link),
			"link": link,
			"answers": frappe.parse_json(booking.answers) or {},
			"record_url": record_url,
			"reason": booking.cancel_reason if action == "cancelled" else "",
			"note": _(
				"There's no Google Meet link because your Google Calendar isn't connected to the CRM. "
				"Send {0} a link to join."
			).format(booking.guest_name)
			if action != "cancelled" and page.location_type == "Google Meet" and not link
			else "",
		},
		reference_doctype="CRM Booking",
		reference_name=booking.name,
	)


def reminder_already_due(booking) -> bool:
	"""No reminder for a meeting booked or moved inside its reminder window:
	the confirmation has only just gone out."""
	offset = REMINDER_OFFSETS.get(
		frappe.db.get_value("CRM Booking Page", booking.booking_page, "guest_reminder")
	)
	return not offset or to_utc(booking.starts_on) - offset <= datetime.now(UTC)


def send_guest_reminders():
	"""Email guests ahead of their meetings, as each page asks. Runs from the scheduler."""
	now = datetime.now(UTC)
	for option, offset in REMINDER_OFFSETS.items():
		pages = frappe.get_all("CRM Booking Page", filters={"guest_reminder": option}, pluck="name")
		due = pages and frappe.get_all(
			"CRM Booking",
			filters={
				"booking_page": ["in", pages],
				"status": "Confirmed",
				"reminder_sent": 0,
				"starts_on": ["between", [to_system(now), to_system(now + offset)]],
			},
			pluck="name",
		)
		for name in due or []:
			booking = frappe.get_doc("CRM Booking", name)
			booking.db_set("reminder_sent", 1, update_modified=False)
			page = frappe.get_doc("CRM Booking Page", booking.booking_page)
			event = (
				frappe.get_doc("Event", booking.event)
				if booking.event and frappe.db.exists("Event", booking.event)
				else None
			)
			send_booking_emails(page, booking, event, "reminder", to_host=False)


@frappe.whitelist()
def hosts_without_google(users: list | str) -> list[str]:
	"""Hosts whose Google Calendar isn't connected to the CRM (enabled, pushing, and
	authorized), so Google can't block their slots or give their meetings a Meet link."""
	users = frappe.parse_json(users) or []
	calendars = frappe.get_all(
		"Google Calendar",
		filters={"user": ["in", users or [""]], "enable": 1, "push_to_google_calendar": 1},
		fields=["name", "user"],
	)
	# Google's callback saves the token on the record itself, so ask the document
	connected = {
		c.user
		for c in calendars
		if frappe.get_doc("Google Calendar", c.name).get_password("refresh_token", raise_exception=False)
	}
	return [u for u in users if u not in connected]


@frappe.whitelist()
def google_status(users: list | str) -> dict:
	"""For a page's settings: whether Google is set up on the site, which hosts haven't
	connected their calendar, and the current user's own Google Calendar record."""
	users = frappe.parse_json(users) or []
	configured = bool(frappe.db.get_single_value("Google Settings", "enable"))
	return {
		"configured": configured,
		"can_set_up": "System Manager" in frappe.get_roles(),
		"unconnected": hosts_without_google(users) if configured else users,
		"my_calendar": frappe.db.get_value("Google Calendar", {"user": frappe.session.user}, "name"),
	}


def notify_host(page, booking, action: str):
	"""An in-app notification for the host, opening the lead or deal's events.

	When someone else owns the lead or deal, they hear about the meeting too."""
	if not booking.reference_docname:
		return
	esc = frappe.utils.escape_html
	guest = f'<span class="font-medium text-ink-gray-9">{esc(booking.guest_name)}</span>'
	title = f'<span class="font-medium text-ink-gray-9">{esc(page.title)}</span>'
	what = {
		"confirmed": _("{0} booked {1}"),
		"rescheduled": _("{0} moved {1}"),
		"cancelled": _("{0} cancelled {1}"),
	}[action].format(guest, title)
	add_booking_notification(booking, booking.host, what)

	owner = record_owner(booking)
	if owner and owner != booking.host:
		host_name = frappe.utils.get_fullname(booking.host)
		with_host = _("{0} with {1}").format(
			what, f'<span class="font-medium text-ink-gray-9">{esc(host_name)}</span>'
		)
		add_booking_notification(booking, owner, with_host)


def add_booking_notification(booking, user: str, what: str):
	user_tz = frappe.db.get_value("User", user, "time_zone") or get_system_timezone()
	frappe.get_doc(
		{
			"doctype": "CRM Notification",
			"from_user": "Guest",
			"to_user": user,
			"type": "Booking",
			"message": frappe.utils.strip_html(what),
			"notification_text": f'<div class="mb-2 leading-5 text-ink-gray-5">{what} · '
			f"{frappe.utils.escape_html(format_short_when(booking, user_tz))}</div>",
			"notification_type_doctype": "CRM Booking",
			"notification_type_doc": booking.name,
			"reference_doctype": booking.reference_doctype,
			"reference_name": booking.reference_docname,
		}
	).insert(ignore_permissions=True)


def record_owner(booking) -> str | None:
	field = "lead_owner" if booking.reference_doctype == "CRM Lead" else "deal_owner"
	return frappe.db.get_value(booking.reference_doctype, booking.reference_docname, field)


def format_short_when(booking, tz_name) -> str:
	start = to_utc(booking.starts_on).astimezone(ZoneInfo(valid_timezone(tz_name) or get_system_timezone()))
	return f"{start:%a %-d %b, %-I:%M %p}"


def location_text(page, link) -> str:
	if page.location_type == "Google Meet":
		return link or _("Google Meet (link to follow)")
	if page.location_type == "Phone call":
		return _("Phone call")
	return page.location or page.location_type


def format_when(booking, tz_name) -> str:
	tz = ZoneInfo(valid_timezone(tz_name) or get_system_timezone())
	start = to_utc(booking.starts_on).astimezone(tz)
	end = to_utc(booking.ends_on).astimezone(tz)
	return f"{start:%A, %-d %B %Y}, {start:%-I:%M %p} – {end:%-I:%M %p} ({tz.key})"


def ics(page, booking, host_name, host_email, link) -> str:
	def stamp(dt):
		return dt.strftime("%Y%m%dT%H%M%SZ")

	def text(value):
		return (
			(value or "")
			.replace("\r", "")
			.replace("\\", "\\\\")
			.replace(";", "\\;")
			.replace(",", "\\,")
			.replace("\n", "\\n")
		)

	def name(value):
		# a parameter value: quoted, so ; : , can't start a new parameter, and no quotes or line breaks inside
		return '"' + re.sub(r'["\r\n]', "", value or "") + '"'

	return "\r\n".join(
		[
			"BEGIN:VCALENDAR",
			"VERSION:2.0",
			"PRODID:-//Frappe CRM//Booking//EN",
			"METHOD:REQUEST",
			"BEGIN:VEVENT",
			f"UID:{booking.name}@{frappe.local.site}",
			f"DTSTAMP:{stamp(datetime.now(UTC))}",
			f"DTSTART:{stamp(to_utc(booking.starts_on))}",
			f"DTEND:{stamp(to_utc(booking.ends_on))}",
			f"SUMMARY:{text(page.title + ' with ' + host_name)}",
			f"LOCATION:{text(location_text(page, link))}",
			f"ORGANIZER;CN={name(host_name)}:mailto:{host_email}",
			f"ATTENDEE;CN={name(booking.guest_name)};RSVP=FALSE:mailto:{booking.guest_email}",
			"END:VEVENT",
			"END:VCALENDAR",
			"",
		]
	)


# Time


def page_timezone(page) -> str:
	return valid_timezone(page.timezone) or get_system_timezone()


def valid_timezone(name: str | None) -> str | None:
	if not name:
		return None
	try:
		ZoneInfo(name)
	except (ZoneInfoNotFoundError, ValueError):
		return None
	return name


def parse_utc(value: str) -> datetime:
	try:
		dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
	except ValueError:
		frappe.throw(_("Invalid time"))
	if dt.tzinfo is None:
		frappe.throw(_("Time must include a timezone"))
	return dt.astimezone(UTC)


def to_iso(dt: datetime) -> str:
	return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def to_utc(value) -> datetime:
	"""A naive datetime in the system timezone, as UTC."""
	return get_datetime(value).replace(tzinfo=ZoneInfo(get_system_timezone())).astimezone(UTC)


def to_system(dt: datetime):
	"""A UTC datetime, as a naive datetime in the system timezone."""
	return dt.astimezone(ZoneInfo(get_system_timezone())).replace(tzinfo=None)
