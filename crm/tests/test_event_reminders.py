# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime

from crm.api.event import purge_event_reminder_logs, trigger_offset_event_notifications
from crm.tests.test_password_setup import make_user


class TestEventReminders(IntegrationTestCase):
	def setUp(self):
		# The job reads every event: park the site's own, so a run never reaches real users.
		frappe.db.sql("UPDATE `tabEvent` SET status = 'Cancelled'")
		self.owner = make_user("reminder-owner-3283@example.com", roles=["Sales User"]).name
		self.participant = make_user("reminder-guest-3283@example.com", roles=["Sales User"]).name
		self.bystander = make_user("reminder-bystander-3283@example.com", roles=["Sales User"]).name

	def tearDown(self):
		frappe.db.rollback()

	def make_customer(self):
		email = "customer-3283@example.org"
		contact = frappe.get_doc(
			doctype="Contact", first_name="Customer 3283", email_ids=[{"email_id": email, "is_primary": 1}]
		).insert(ignore_permissions=True)
		return {"reference_doctype": "Contact", "reference_docname": contact.name, "email": email}

	def make_event(self, participants=(), customers=(), notifications=True, starts_on=None, **fields):
		event = frappe.get_doc(
			doctype="Event",
			subject="Reminder 3283",
			event_type="Private",
			starts_on=starts_on or add_to_date(now_datetime(), minutes=10),
			event_participants=[
				*(
					{"reference_doctype": "User", "reference_docname": email, "email": email}
					for email in participants
				),
				*customers,
			],
			**fields,
			notifications=[{"type": "Notification", "before": 10, "interval": "minutes"}]
			if notifications
			else [],
		).insert(ignore_permissions=True)
		frappe.db.set_value("Event", event.name, "owner", self.owner)
		return event

	def run_scheduler_job(self, event):
		"""Run the job as the scheduler does and return the recipients of the event's reminders."""
		self.assertEqual(frappe.session.user, "Administrator")
		with patch("frappe.publish_realtime") as publish_realtime:
			trigger_offset_event_notifications()
		return [
			call.kwargs["user"]
			for call in publish_realtime.call_args_list
			if isinstance(call.args[1], dict) and call.args[1].get("event_name") == event.name
		]

	def test_a_reminder_for_a_normal_users_event_reaches_the_scheduler_job(self):
		event = self.make_event()

		self.assertEqual(self.run_scheduler_job(event), [self.owner])

	def test_a_reminder_goes_to_the_owner_and_the_participants_once_each(self):
		event = self.make_event(participants=[self.participant], customers=[self.make_customer()])

		recipients = self.run_scheduler_job(event)

		self.assertEqual(len(recipients), len(set(recipients)))
		self.assertTrue({self.owner, self.participant} <= set(recipients))
		self.assertNotIn(self.bystander, recipients)

	def test_a_global_reminder_reaches_a_normal_users_event_too(self):
		event = self.make_event(participants=[self.participant], notifications=False)
		global_notification = frappe._dict(type="Notification", interval="minutes", before=10, time=None)
		settings = frappe._dict(event_notifications=[global_notification], all_day_event_notifications=[])

		with patch("frappe.get_single", return_value=settings):
			recipients = self.run_scheduler_job(event)

		self.assertCountEqual(recipients, [self.owner, self.participant])

	def test_a_cancelled_event_gets_no_reminder(self):
		event = self.make_event(status="Cancelled")

		self.assertEqual(self.run_scheduler_job(event), [])

	def test_an_event_outside_the_reminder_window_gets_no_reminder(self):
		event = self.make_event(starts_on=add_to_date(now_datetime(), days=2))

		self.assertEqual(self.run_scheduler_job(event), [])

	def test_an_email_reminder_goes_to_the_owner_and_the_participants(self):
		event = self.make_event(participants=[self.participant], customers=[self.make_customer()])
		frappe.db.set_value("Event Notifications", {"parent": event.name}, "type", "Email")

		with patch("frappe.sendmail") as sendmail:
			self.run_scheduler_job(event)

		self.assertCountEqual(
			sendmail.call_args.kwargs["recipients"],
			[self.owner, self.participant, "customer-3283@example.org"],
		)

	def test_a_reminder_inside_its_window_reaches_each_recipient_once_over_several_runs(self):
		event = self.make_event(participants=[self.participant])

		recipients = [self.run_scheduler_job(event) for _ in range(3)]

		self.assertCountEqual(recipients[0], [self.owner, self.participant])
		self.assertEqual(recipients[1:], [[], []])

	def test_an_email_reminder_is_sent_once_over_several_runs(self):
		event = self.make_event(participants=[self.participant])
		frappe.db.set_value("Event Notifications", {"parent": event.name}, "type", "Email")

		with patch("frappe.sendmail") as sendmail:
			for _ in range(3):
				self.run_scheduler_job(event)

		self.assertEqual(sendmail.call_count, 1)

	def test_an_event_in_progress_gets_its_reminder_once_over_several_runs(self):
		event = self.make_event(
			starts_on=add_to_date(now_datetime(), minutes=-30), ends_on=add_to_date(now_datetime(), hours=1)
		)

		recipients = [self.run_scheduler_job(event) for _ in range(3)]

		self.assertEqual(recipients, [[self.owner], [], []])

	def test_a_rescheduled_event_gets_its_reminder_again(self):
		event = self.make_event()
		self.assertEqual(self.run_scheduler_job(event), [self.owner])

		frappe.db.set_value("Event", event.name, "starts_on", add_to_date(now_datetime(), minutes=11))

		self.assertEqual(self.run_scheduler_job(event), [self.owner])

	def test_a_second_reminder_row_is_not_swallowed_by_the_first(self):
		event = self.make_event()
		event.reload()
		event.append("notifications", {"type": "Notification", "before": 11, "interval": "minutes"})
		event.save(ignore_permissions=True)

		self.assertEqual(self.run_scheduler_job(event), [self.owner, self.owner])
		self.assertEqual(self.run_scheduler_job(event), [])

	def test_the_scan_leaves_out_events_that_start_after_the_longest_reminder_offset(self):
		near = self.make_event()
		far = self.make_event(starts_on=add_to_date(now_datetime(), days=10))

		with patch("crm.api.event._process_unified_event_data", return_value=[]) as process:
			self.run_scheduler_job(near)

		scanned = {row.event_name for row in process.call_args.args[0]}
		self.assertIn(near.name, scanned)
		self.assertNotIn(far.name, scanned)

	def test_purge_keeps_the_markers_of_a_live_event_and_drops_the_rest(self):
		live = self.make_event()
		ended = self.make_event(
			starts_on=add_to_date(now_datetime(), days=-3), ends_on=add_to_date(now_datetime(), days=-2)
		)
		self.run_scheduler_job(live)
		stale = frappe.get_doc(
			doctype="CRM Event Reminder Log",
			reminder_key="stale-3306",
			event=ended.name,
			recipient=self.owner,
		).insert(ignore_permissions=True)

		purge_event_reminder_logs()

		kept = frappe.get_all("CRM Event Reminder Log", {"event": live.name}, pluck="name")
		self.assertEqual(len(kept), 1)
		self.assertFalse(frappe.db.exists("CRM Event Reminder Log", stale.name))
