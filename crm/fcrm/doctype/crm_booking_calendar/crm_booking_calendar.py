# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import datetime
import re
from zoneinfo import ZoneInfo

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, get_system_timezone, now_datetime

UTC = datetime.timezone.utc

# All slot math is timezone-aware and returned in UTC; booking rows persist naive
# datetimes in the site's system timezone (the framework-wide convention).


def system_tz() -> ZoneInfo:
	return ZoneInfo(get_system_timezone())


def to_system_naive(aware: datetime.datetime) -> datetime.datetime:
	return aware.astimezone(system_tz()).replace(tzinfo=None)


def from_system_naive(naive) -> datetime.datetime:
	from frappe.utils import get_datetime

	return get_datetime(naive).replace(tzinfo=system_tz()).astimezone(UTC)


class CRMBookingCalendar(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.fcrm.doctype.crm_booking_calendar_member.crm_booking_calendar_member import (
			CRMBookingCalendarMember,
		)
		from crm.fcrm.doctype.crm_service_day.crm_service_day import CRMServiceDay

		availability: DF.Table[CRMServiceDay]
		buffer_after: DF.Int
		buffer_before: DF.Int
		calendar_name: DF.Data
		description: DF.SmallText | None
		distribution: DF.Literal["Round Robin"]
		duration: DF.Int
		enabled: DF.Check
		holiday_list: DF.Link | None
		location: DF.Data | None
		max_horizon_days: DF.Int
		members: DF.Table[CRMBookingCalendarMember]
		min_notice_hours: DF.Int
		route: DF.Data
		slot_interval: DF.Int
		timezone: DF.Data
	# end: auto-generated types

	def validate(self):
		self.validate_route()
		self.validate_timezone()
		self.validate_numbers()
		self.validate_availability()
		self.validate_members()

	def validate_route(self):
		self.route = (self.route or "").strip().strip("/").lower()
		if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", self.route):
			frappe.throw(_("Route must contain only lowercase letters, numbers and hyphens"))

	def validate_timezone(self):
		try:
			ZoneInfo(self.timezone)
		except Exception:
			frappe.throw(_("{0} is not a valid IANA timezone (e.g. Europe/Rome)").format(self.timezone))

	def validate_numbers(self):
		if cint(self.duration) <= 0:
			frappe.throw(_("Duration must be a positive number of minutes"))
		for field, label in (
			("slot_interval", _("Slot Interval")),
			("buffer_before", _("Buffer Before")),
			("buffer_after", _("Buffer After")),
			("min_notice_hours", _("Minimum Notice")),
		):
			if cint(self.get(field)) < 0:
				frappe.throw(_("{0} cannot be negative").format(label))
		if cint(self.max_horizon_days) <= 0:
			frappe.throw(_("Booking Horizon must be at least 1 day"))

	def validate_availability(self):
		for row in self.availability:
			if row.start_time >= row.end_time:
				frappe.throw(_("Row {0}: availability start time must be before end time").format(row.idx))

	def validate_members(self):
		seen = set()
		for row in self.members:
			if row.user in seen:
				frappe.throw(_("{0} is listed more than once in Members").format(row.user))
			seen.add(row.user)

	# --- slot computation -------------------------------------------------

	def booking_window_utc(self) -> tuple[datetime.datetime, datetime.datetime]:
		"""Earliest and latest bookable instant: now + notice → now + horizon."""
		now = now_datetime().replace(tzinfo=system_tz()).astimezone(UTC)
		earliest = now + datetime.timedelta(hours=cint(self.min_notice_hours))
		latest = now + datetime.timedelta(days=cint(self.max_horizon_days))
		return earliest, latest

	def get_available_slots(self, from_date: datetime.date, to_date: datetime.date) -> list[dict]:
		"""Free slots between the two dates (calendar-timezone days), as
		[{"start": aware-UTC datetime, "free_members": [user, ...]}], sorted."""
		cal_tz = ZoneInfo(self.timezone)
		earliest, latest = self.booking_window_utc()
		duration = datetime.timedelta(minutes=cint(self.duration))
		step = datetime.timedelta(minutes=cint(self.slot_interval) or cint(self.duration))
		members = [m.user for m in self.members]
		holidays = self.get_holiday_dates()
		busy = self.get_busy_intervals(members, earliest, latest + duration)

		windows_by_day: dict[str, list] = {}
		for row in self.availability:
			windows_by_day.setdefault(row.workday, []).append(row)

		slots = []
		day = from_date
		while day <= to_date:
			if day not in holidays:
				for row in windows_by_day.get(day.strftime("%A"), []):
					win_start = datetime.datetime.combine(
						day, _as_time(row.start_time), tzinfo=cal_tz
					).astimezone(UTC)
					win_end = datetime.datetime.combine(
						day, _as_time(row.end_time), tzinfo=cal_tz
					).astimezone(UTC)
					cursor = win_start
					while cursor + duration <= win_end:
						if earliest <= cursor <= latest:
							free = [
								u
								for u in members
								if not _overlaps(busy.get(u, []), cursor, cursor + duration)
							]
							if free:
								slots.append({"start": cursor, "free_members": free})
						cursor += step
			day += datetime.timedelta(days=1)

		slots.sort(key=lambda s: s["start"])
		return slots

	def get_holiday_dates(self) -> set[datetime.date]:
		if not self.holiday_list:
			return set()
		dates = frappe.get_all("CRM Holiday", filters={"parent": self.holiday_list}, pluck="date")
		return set(dates)

	def get_busy_intervals(
		self, members: list[str], start: datetime.datetime, end: datetime.datetime
	) -> dict[str, list[tuple[datetime.datetime, datetime.datetime]]]:
		"""Confirmed bookings of these members across ALL calendars, expanded by
		this calendar's buffers, keyed by member, as aware-UTC intervals."""
		if not members:
			return {}
		before = datetime.timedelta(minutes=cint(self.buffer_before))
		after = datetime.timedelta(minutes=cint(self.buffer_after))
		rows = frappe.get_all(
			"CRM Booking",
			filters={
				"agent": ["in", members],
				"status": "Confirmed",
				"starts_on": ["<", to_system_naive(end + before)],
				"ends_on": [">", to_system_naive(start - after)],
			},
			fields=["agent", "starts_on", "ends_on"],
		)
		busy: dict[str, list] = {}
		for row in rows:
			busy.setdefault(row.agent, []).append(
				(from_system_naive(row.starts_on) - before, from_system_naive(row.ends_on) + after)
			)
		return busy

	def is_slot_available(self, start_utc: datetime.datetime) -> list[str]:
		"""Free members for one exact slot start (aware UTC); [] if unavailable."""
		day = start_utc.astimezone(ZoneInfo(self.timezone)).date()
		for slot in self.get_available_slots(day, day):
			if slot["start"] == start_utc:
				return slot["free_members"]
		return []

	def pick_agent(self, free_members: list[str]) -> str:
		"""Round robin: the free member with the fewest upcoming confirmed bookings."""
		if len(free_members) == 1:
			return free_members[0]
		counts = dict.fromkeys(free_members, 0)
		rows = frappe.get_all(
			"CRM Booking",
			filters={
				"agent": ["in", free_members],
				"status": "Confirmed",
				"starts_on": [">=", now_datetime()],
			},
			fields=["agent", "count(name) as total"],
			group_by="agent",
		)
		for row in rows:
			counts[row.agent] = row.total
		return min(free_members, key=lambda u: counts[u])


def _as_time(value) -> datetime.time:
	"""Child-table Time fields load as timedelta from the DB but time from forms."""
	if isinstance(value, datetime.timedelta):
		return (datetime.datetime.min + value).time()
	if isinstance(value, str):
		return datetime.time.fromisoformat(value)
	return value


def _overlaps(intervals, start, end) -> bool:
	return any(s < end and e > start for s, e in intervals)
