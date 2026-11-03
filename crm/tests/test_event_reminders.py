# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime

from crm.api.event import trigger_offset_event_notifications
from crm.tests.test_password_setup import make_user


class TestEventReminders(IntegrationTestCase):
	def setUp(self):
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
