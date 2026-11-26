from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime

PUSH = "frappe.integrations.doctype.google_calendar.google_calendar.insert_event_in_google_calendar"


def new_event(**values):
	start = add_to_date(now_datetime(), days=1)
	return frappe.get_doc(
		{
			"doctype": "Event",
			"subject": "Google sync test",
			"event_type": "Private",
			"starts_on": start,
			"ends_on": add_to_date(start, hours=1),
			**values,
		}
	).insert()


class TestEventGoogleSync(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# skips Google Settings validation; nothing here talks to Google
		frappe.get_doc(
			{
				"doctype": "Google Calendar",
				"name": "_Test Calendar",
				"calendar_name": "_Test Calendar",
				"user": "Administrator",
				"enable": 1,
				"push_to_google_calendar": 1,
				"google_calendar_id": "test@group.calendar.google.com",
			}
		).db_insert()

	def setUp(self):
		frappe.set_user("Administrator")
		self.pushed = []

	def record_push(self, doc, method=None):
		# Frappe's own after_insert calls the same function; count only real pushes
		if doc.sync_with_google_calendar:
			self.pushed.append(doc.name)

	def test_no_connected_calendar_saves_without_sync(self):
		with (
			patch("crm.api.event.connected_google_calendar", return_value=None),
			patch(PUSH, self.record_push),
		):
			event = new_event(sync_with_google_calendar=1)
		event.reload()
		self.assertFalse(event.sync_with_google_calendar)
		self.assertFalse(event.google_calendar)
		self.assertEqual(self.pushed, [])

	def test_connected_calendar_pushes_and_keeps_sync(self):
		with (
			patch("crm.api.event.connected_google_calendar", return_value="_Test Calendar"),
			patch(PUSH, self.record_push),
		):
			event = new_event(sync_with_google_calendar=1)
		self.assertEqual(self.pushed, [event.name])
		self.assertEqual(frappe.db.get_value("Event", event.name, "sync_with_google_calendar"), 1)
		self.assertEqual(frappe.db.get_value("Event", event.name, "google_calendar"), "_Test Calendar")

	def test_google_error_still_creates_event(self):
		def fail(doc, method=None):
			if doc.sync_with_google_calendar:
				frappe.throw("Google said no")

		with (
			patch("crm.api.event.connected_google_calendar", return_value="_Test Calendar"),
			patch(PUSH, fail),
		):
			event = new_event(sync_with_google_calendar=1)
		self.assertTrue(frappe.db.exists("Event", event.name))
		self.assertEqual(frappe.db.get_value("Event", event.name, "sync_with_google_calendar"), 0)
		self.assertFalse(frappe.db.get_value("Event", event.name, "google_calendar"))

	def test_events_not_asking_for_sync_are_left_alone(self):
		with patch("crm.api.event.connected_google_calendar") as connected, patch(PUSH, self.record_push):
			new_event()
		connected.assert_not_called()
		self.assertEqual(self.pushed, [])

	def test_event_with_a_calendar_already_picked_is_not_held(self):
		event = frappe.new_doc("Event")
		event.update({"sync_with_google_calendar": 1, "google_calendar": "_Test Calendar"})
		from crm.api.event import hold_google_sync

		hold_google_sync(event)
		self.assertEqual(event.sync_with_google_calendar, 1)
		self.assertFalse(event.flags.push_to_google)

	def test_editing_an_event_that_asks_for_sync_still_saves(self):
		with (
			patch("crm.api.event.connected_google_calendar", return_value="_Test Calendar"),
			patch(PUSH, self.record_push),
		):
			event = new_event()
			event.sync_with_google_calendar = 1
			event.save()
		self.assertEqual(frappe.db.get_value("Event", event.name, "sync_with_google_calendar"), 0)
		self.assertEqual(self.pushed, [])

	def test_calendar_not_yet_made_in_google_is_not_pushed(self):
		frappe.db.set_value("Google Calendar", "_Test Calendar", "google_calendar_id", "")
		try:
			with (
				patch("crm.api.event.connected_google_calendar", return_value="_Test Calendar"),
				patch(PUSH, self.record_push),
			):
				event = new_event(sync_with_google_calendar=1)
		finally:
			frappe.db.set_value(
				"Google Calendar", "_Test Calendar", "google_calendar_id", "test@group.calendar.google.com"
			)
		self.assertEqual(self.pushed, [])
		self.assertEqual(frappe.db.get_value("Event", event.name, "sync_with_google_calendar"), 0)
		self.assertFalse(frappe.db.get_value("Event", event.name, "google_calendar"))
