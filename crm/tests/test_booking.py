# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import datetime

import frappe
from frappe.tests import IntegrationTestCase

from crm.api import booking as B
from crm.fcrm.doctype.crm_booking_calendar.crm_booking_calendar import from_system_naive

ALL_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def make_calendar(route="test-cal", **kw):
	payload = {
		"doctype": "CRM Booking Calendar",
		"calendar_name": kw.pop("calendar_name", f"Test Calendar {route}"),
		"route": route,
		"enabled": 1,
		"timezone": "UTC",
		"duration": 30,
		"min_notice_hours": 0,
		"max_horizon_days": 7,
		"members": [{"user": "Administrator"}],
		# open all day, every day, so tests are independent of when they run
		"availability": [{"workday": d, "start_time": "00:00:00", "end_time": "23:59:59"} for d in ALL_DAYS],
	}
	payload.update(kw)
	return frappe.get_doc(payload).insert()


def first_slot(route):
	cal = frappe.get_doc("CRM Booking Calendar", {"route": route})
	today = datetime.date.today()
	slots = cal.get_available_slots(today, today + datetime.timedelta(days=2))
	assert slots, "expected at least one free slot"
	return slots[0]["start"]


class TestBooking(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	# ---- calendar validation ----

	def test_invalid_timezone_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			make_calendar(route="bad-tz", timezone="Mars/Olympus")

	def test_invalid_route_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			make_calendar(route="Bad Route!")

	def test_availability_start_before_end(self):
		with self.assertRaises(frappe.ValidationError):
			make_calendar(
				route="bad-hours",
				availability=[{"workday": "Monday", "start_time": "18:00:00", "end_time": "09:00:00"}],
			)

	# ---- slots ----

	def test_slots_are_generated(self):
		make_calendar(route="slots-cal")
		start = first_slot("slots-cal")
		self.assertEqual(start.tzinfo is not None, True)
		self.assertEqual(start.minute % 30, 0)

	def test_booked_slot_disappears(self):
		make_calendar(route="busy-cal")
		start = first_slot("busy-cal")
		B.book(
			route="busy-cal",
			start=start.isoformat(),
			invitee_name="Mario Rossi",
			invitee_email="mario@example.com",
		)
		cal = frappe.get_doc("CRM Booking Calendar", {"route": "busy-cal"})
		self.assertEqual(cal.is_slot_available(start), [])

	def test_min_notice_excludes_near_slots(self):
		make_calendar(route="notice-cal", min_notice_hours=48, max_horizon_days=3)
		cal = frappe.get_doc("CRM Booking Calendar", {"route": "notice-cal"})
		today = datetime.date.today()
		slots = cal.get_available_slots(today, today + datetime.timedelta(days=3))
		earliest, _latest = cal.booking_window_utc()
		for slot in slots:
			self.assertGreaterEqual(slot["start"], earliest)

	# ---- booking flow ----

	def test_book_creates_booking_and_lead(self):
		make_calendar(route="flow-cal")
		start = first_slot("flow-cal")
		result = B.book(
			route="flow-cal",
			start=start.isoformat(),
			invitee_name="Anna Bianchi",
			invitee_email="anna@example.com",
			invitee_phone="+390000000000",
			invitee_timezone="Europe/Rome",
		)
		self.assertEqual(result["status"], "Confirmed")
		name = frappe.db.get_value("CRM Booking", {"access_token": result["token"]})
		doc = frappe.get_doc("CRM Booking", name)
		self.assertEqual(doc.agent, "Administrator")
		self.assertEqual(from_system_naive(doc.starts_on), start)
		self.assertTrue(doc.lead)
		lead = frappe.get_doc("CRM Lead", doc.lead)
		self.assertEqual(lead.email, "anna@example.com")
		self.assertEqual(lead.source, B.BOOKING_SOURCE)

	def test_double_booking_same_slot_rejected(self):
		make_calendar(route="dbl-cal")
		start = first_slot("dbl-cal")
		B.book(route="dbl-cal", start=start.isoformat(), invitee_name="A", invitee_email="a@example.com")
		with self.assertRaises(frappe.ValidationError):
			B.book(route="dbl-cal", start=start.isoformat(), invitee_name="B", invitee_email="b@example.com")

	def test_cancel_frees_the_slot(self):
		make_calendar(route="cancel-cal")
		start = first_slot("cancel-cal")
		result = B.book(
			route="cancel-cal", start=start.isoformat(), invitee_name="C", invitee_email="c@example.com"
		)
		B.cancel_booking(token=result["token"])
		cal = frappe.get_doc("CRM Booking Calendar", {"route": "cancel-cal"})
		self.assertEqual(cal.is_slot_available(start), ["Administrator"])

	def test_reschedule_moves_booking(self):
		make_calendar(route="resch-cal")
		cal = frappe.get_doc("CRM Booking Calendar", {"route": "resch-cal"})
		today = datetime.date.today()
		slots = cal.get_available_slots(today, today + datetime.timedelta(days=2))
		self.assertGreaterEqual(len(slots), 2)
		first, second = slots[0]["start"], slots[1]["start"]
		result = B.book(
			route="resch-cal", start=first.isoformat(), invitee_name="D", invitee_email="d@example.com"
		)
		moved = B.reschedule_booking(token=result["token"], start=second.isoformat())
		self.assertEqual(moved["status"], "Confirmed")
		self.assertEqual(moved["start"], second.isoformat())
		# the original slot is free again
		self.assertEqual(cal.is_slot_available(first), ["Administrator"])

	def test_bad_token_rejected(self):
		with self.assertRaises(frappe.PermissionError):
			B.get_booking(token="short")
		with self.assertRaises(frappe.DoesNotExistError):
			B.get_booking(token="x" * 32)

	def test_buffer_blocks_adjacent_slot(self):
		make_calendar(route="buffer-cal", buffer_after=30)
		start = first_slot("buffer-cal")
		B.book(route="buffer-cal", start=start.isoformat(), invitee_name="E", invitee_email="e@example.com")
		cal = frappe.get_doc("CRM Booking Calendar", {"route": "buffer-cal"})
		adjacent = start + datetime.timedelta(minutes=30)
		self.assertEqual(cal.is_slot_available(adjacent), [])
		after_buffer = start + datetime.timedelta(minutes=60)
		self.assertEqual(cal.is_slot_available(after_buffer), ["Administrator"])
