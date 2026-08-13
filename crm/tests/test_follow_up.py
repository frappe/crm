# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.desk.form.assign_to import add as assign_add
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime

from crm.api import follow_up
from crm.api.follow_up import (
	get_due_records,
	get_lead_time,
	get_recipients,
	trigger_follow_up_reminders,
)


class TestFollowUpReminders(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")
		frappe.db.set_single_value("FCRM Settings", "enable_follow_up_reminders", 1)
		frappe.db.set_single_value("FCRM Settings", "follow_up_reminder_before", 30)
		frappe.db.set_single_value("FCRM Settings", "follow_up_reminder_interval", "minutes")
		frappe.db.set_single_value("FCRM Settings", "send_follow_up_reminder_email", 0)
		frappe.clear_cache(doctype="FCRM Settings")

	def tearDown(self) -> None:
		frappe.db.rollback()
		frappe.clear_cache(doctype="FCRM Settings")

	# helpers -----------------------------------------------------------------

	def make_lead(self, **kwargs):
		values = {
			"doctype": "CRM Lead",
			"first_name": "Follow",
			"last_name": "Up",
			"lead_owner": "Administrator",
		}
		values.update(kwargs)
		return frappe.get_doc(values).insert(ignore_permissions=True)

	def reminders_for(self, doctype, name):
		return frappe.get_all(
			"CRM Notification",
			filters={"type": "Follow Up", "reference_doctype": doctype, "reference_name": name},
			fields=["to_user"],
		)

	def flag(self, doctype, name):
		return frappe.db.get_value(doctype, name, "follow_up_reminder_sent")

	# lead time ---------------------------------------------------------------

	def test_lead_time_kwargs(self):
		self.assertEqual(get_lead_time({"follow_up_reminder_before": 30}), {"minutes": 30})
		self.assertEqual(
			get_lead_time({"follow_up_reminder_before": 2, "follow_up_reminder_interval": "hours"}),
			{"hours": 2},
		)
		self.assertEqual(get_lead_time({"follow_up_reminder_before": 0}), {"minutes": 0})
		# an unexpected interval falls back rather than blowing up the scheduler
		self.assertEqual(
			get_lead_time({"follow_up_reminder_before": 5, "follow_up_reminder_interval": "fortnights"}),
			{"minutes": 5},
		)

	# due selection -----------------------------------------------------------

	def test_record_without_follow_up_is_never_due(self):
		lead = self.make_lead()
		cutoff = add_to_date(now_datetime(), minutes=30)
		self.assertNotIn(lead.name, [d.name for d in get_due_records("CRM Lead", cutoff)])

	def test_follow_up_beyond_lead_time_is_not_due(self):
		lead = self.make_lead(next_follow_up=add_to_date(now_datetime(), hours=5))
		trigger_follow_up_reminders()
		self.assertEqual(self.reminders_for("CRM Lead", lead.name), [])
		self.assertEqual(self.flag("CRM Lead", lead.name), 0)

	def test_follow_up_within_lead_time_notifies_and_marks_sent(self):
		lead = self.make_lead(next_follow_up=add_to_date(now_datetime(), minutes=10))
		trigger_follow_up_reminders()

		self.assertEqual([r.to_user for r in self.reminders_for("CRM Lead", lead.name)], ["Administrator"])
		self.assertEqual(self.flag("CRM Lead", lead.name), 1)

	def test_overdue_follow_up_still_notifies(self):
		lead = self.make_lead(next_follow_up=add_to_date(now_datetime(), hours=-3))
		trigger_follow_up_reminders()
		self.assertEqual(len(self.reminders_for("CRM Lead", lead.name)), 1)

	def test_reminder_is_not_sent_twice(self):
		lead = self.make_lead(next_follow_up=add_to_date(now_datetime(), minutes=10))
		trigger_follow_up_reminders()
		trigger_follow_up_reminders()
		self.assertEqual(len(self.reminders_for("CRM Lead", lead.name)), 1)

	# lifecycle ---------------------------------------------------------------

	def test_rescheduling_clears_the_sent_flag(self):
		lead = self.make_lead(next_follow_up=add_to_date(now_datetime(), minutes=10))
		trigger_follow_up_reminders()
		self.assertEqual(self.flag("CRM Lead", lead.name), 1)

		lead.reload()
		lead.next_follow_up = add_to_date(now_datetime(), days=2)
		lead.save(ignore_permissions=True)
		self.assertEqual(self.flag("CRM Lead", lead.name), 0)

	def test_clearing_the_date_drops_the_reminder(self):
		lead = self.make_lead(next_follow_up=add_to_date(now_datetime(), minutes=10))
		trigger_follow_up_reminders()
		sent = len(self.reminders_for("CRM Lead", lead.name))

		lead.reload()
		lead.next_follow_up = None
		lead.save(ignore_permissions=True)
		self.assertEqual(self.flag("CRM Lead", lead.name), 0)

		trigger_follow_up_reminders()
		self.assertEqual(len(self.reminders_for("CRM Lead", lead.name)), sent)
		# a record with no date must never be picked up, flag or not
		self.assertEqual(self.flag("CRM Lead", lead.name), 0)

	def test_closed_deal_is_skipped(self):
		lost = frappe.get_all("CRM Deal Status", filters={"type": "Lost"}, pluck="name")
		if not lost:
			self.skipTest("no Lost deal status configured")

		deal = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"deal_owner": "Administrator",
				"next_follow_up": add_to_date(now_datetime(), minutes=10),
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value("CRM Deal", deal.name, "status", lost[0], update_modified=False)

		trigger_follow_up_reminders()
		self.assertEqual(self.reminders_for("CRM Deal", deal.name), [])
		self.assertEqual(self.flag("CRM Deal", deal.name), 0)

	def test_converted_lead_is_skipped(self):
		lead = self.make_lead(next_follow_up=add_to_date(now_datetime(), minutes=10))
		frappe.db.set_value("CRM Lead", lead.name, "converted", 1, update_modified=False)

		trigger_follow_up_reminders()
		self.assertEqual(self.reminders_for("CRM Lead", lead.name), [])

	def test_disabled_setting_is_a_no_op(self):
		frappe.db.set_single_value("FCRM Settings", "enable_follow_up_reminders", 0)
		frappe.clear_cache(doctype="FCRM Settings")

		lead = self.make_lead(next_follow_up=add_to_date(now_datetime(), minutes=10))
		trigger_follow_up_reminders()

		self.assertEqual(self.reminders_for("CRM Lead", lead.name), [])
		self.assertEqual(self.flag("CRM Lead", lead.name), 0)

	# recipients --------------------------------------------------------------

	def test_assigned_users_get_the_reminder(self):
		user = create_test_user("follow.up.rep@example.com")
		lead = self.make_lead(next_follow_up=add_to_date(now_datetime(), minutes=10))
		assign_add(
			{
				"doctype": "CRM Lead",
				"name": lead.name,
				"assign_to": [user.name],
			}
		)

		trigger_follow_up_reminders()
		self.assertIn(user.name, [r.to_user for r in self.reminders_for("CRM Lead", lead.name)])

	def test_falls_back_to_owner_when_unassigned(self):
		lead = self.make_lead(lead_owner=None, next_follow_up=add_to_date(now_datetime(), minutes=10))
		frappe.db.set_value("CRM Lead", lead.name, "_assign", None, update_modified=False)

		lead.reload()
		recipients = get_recipients("CRM Lead", frappe._dict(lead.as_dict()))
		self.assertEqual(recipients, [lead.owner])

	# failure isolation ------------------------------------------------------

	def test_one_failing_recipient_does_not_cost_the_others(self):
		good = create_test_user("follow.up.good@example.com")
		bad = create_test_user("follow.up.bad@example.com")
		lead = self.make_lead(next_follow_up=add_to_date(now_datetime(), minutes=10))
		frappe.db.set_value(
			"CRM Lead", lead.name, "_assign", frappe.as_json([bad.name, good.name]), update_modified=False
		)

		real_notify = follow_up.notify_user

		def flaky(notification):
			if notification["assigned_to"] == bad.name:
				raise ValueError("boom")
			return real_notify(notification)

		with patch.object(follow_up, "notify_user", side_effect=flaky):
			trigger_follow_up_reminders()

		notified = [r.to_user for r in self.reminders_for("CRM Lead", lead.name)]
		self.assertEqual(notified, [good.name])
		# the good recipient's reminder survived, so the record is done
		self.assertEqual(self.flag("CRM Lead", lead.name), 1)

	def test_record_is_retried_when_nothing_could_be_sent(self):
		lead = self.make_lead(next_follow_up=add_to_date(now_datetime(), minutes=10))

		with patch.object(follow_up, "get_recipients", side_effect=ValueError("boom")):
			trigger_follow_up_reminders()

		self.assertEqual(self.reminders_for("CRM Lead", lead.name), [])
		# nothing went out, so the flag stays clear and the next tick retries
		self.assertEqual(self.flag("CRM Lead", lead.name), 0)

		trigger_follow_up_reminders()
		self.assertEqual(len(self.reminders_for("CRM Lead", lead.name)), 1)

	def test_email_failure_does_not_cost_the_in_app_reminder(self):
		frappe.db.set_single_value("FCRM Settings", "send_follow_up_reminder_email", 1)
		frappe.clear_cache(doctype="FCRM Settings")
		lead = self.make_lead(next_follow_up=add_to_date(now_datetime(), minutes=10))

		with patch.object(follow_up, "send_reminder_email", side_effect=ValueError("boom")):
			trigger_follow_up_reminders()

		self.assertEqual(len(self.reminders_for("CRM Lead", lead.name)), 1)
		self.assertEqual(self.flag("CRM Lead", lead.name), 1)

	def test_disabled_users_are_dropped(self):
		user = create_test_user("follow.up.gone@example.com")
		frappe.db.set_value("User", user.name, "enabled", 0)

		record = frappe._dict(name="dummy", _assign=frappe.as_json([user.name]), owner="Administrator")
		self.assertEqual(get_recipients("CRM Lead", record), [])


def create_test_user(email):
	if frappe.db.exists("User", email):
		user = frappe.get_doc("User", email)
		user.enabled = 1
		user.save(ignore_permissions=True)
		return user

	return frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": email.split("@")[0],
			"send_welcome_email": 0,
			"roles": [{"role": "Sales User"}],
		}
	).insert(ignore_permissions=True)
