from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, add_to_date, now_datetime, nowdate

from crm.fcrm.doctype.crm_task.reminders import send_follow_up_reminders
from crm.tests.test_home import AGENT, make_lead, make_task, make_user


def in_minutes(minutes: int):
	return add_to_date(now_datetime(), minutes=minutes)


def reminders():
	return frappe.get_all(
		"CRM Notification",
		filters={"type": "Reminder"},
		fields=["to_user", "notification_type_doc", "reference_doctype", "reference_name"],
	)


class TestFollowUpReminders(IntegrationTestCase):
	def setUp(self):
		make_user(AGENT, "Sales User")
		self.lead = make_lead()
		frappe.db.delete("CRM Notification", {"type": "Reminder"})

	def tearDown(self):
		frappe.db.rollback()

	def follow_up(self, due_date, **kwargs):
		linked = {"reference_doctype": "CRM Lead", "reference_docname": self.lead, "assigned_to": AGENT}
		return make_task(due_date, **{**linked, **kwargs})

	def test_reminds_the_assignee_within_fifteen_minutes(self):
		task = self.follow_up(in_minutes(10))
		self.follow_up(in_minutes(20))

		send_follow_up_reminders()

		rows = reminders()
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0].to_user, AGENT)
		self.assertEqual(rows[0].notification_type_doc, str(task.name))
		self.assertEqual((rows[0].reference_doctype, rows[0].reference_name), ("CRM Lead", self.lead))

	def test_skips_overdue_all_day_closed_unassigned_and_standalone_tasks(self):
		self.follow_up(in_minutes(-1))
		self.follow_up(nowdate(), all_day=1)
		self.follow_up(in_minutes(10), status="Done")
		self.follow_up(in_minutes(10), assigned_to=None)
		make_task(in_minutes(10), assigned_to=AGENT)

		send_follow_up_reminders()

		self.assertEqual(reminders(), [])

	def test_reminds_once_per_due_time(self):
		self.follow_up(in_minutes(10))
		send_follow_up_reminders()
		send_follow_up_reminders()
		self.assertEqual(len(reminders()), 1)

	def test_rescheduling_arms_a_new_reminder(self):
		task = self.follow_up(in_minutes(10))
		send_follow_up_reminders()

		task.reload()
		task.due_date = in_minutes(12)
		task.save()
		send_follow_up_reminders()

		self.assertEqual(len(reminders()), 2)

	def test_rescheduling_to_the_same_time_next_day_reminds_again(self):
		task = self.follow_up(in_minutes(10))
		send_follow_up_reminders()

		task.reload()
		task.due_date = add_days(task.due_date, 1)
		task.save()
		with patch(
			"crm.fcrm.doctype.crm_task.reminders.now_datetime", return_value=add_days(now_datetime(), 1)
		):
			send_follow_up_reminders()

		self.assertEqual(len(reminders()), 2)
