from functools import partial
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import get_datetime

from crm.fcrm.doctype.crm_task.rules import TaskDue, is_follow_up, went_overdue_between

RULES = "crm.fcrm.doctype.crm_task.rules"


def rules(now: str, user_zone: str = "UTC", system_zone: str = "UTC") -> TaskDue:
	with (
		patch(f"{RULES}.get_system_timezone", return_value=system_zone),
		patch(f"{RULES}._user_time_zone", return_value=user_zone),
	):
		return TaskDue(now=get_datetime(now))


def task(due_date, all_day=0, status="Todo", **kwargs):
	return frappe._dict(due_date=due_date, all_day=all_day, status=status, **kwargs)


class TestTaskDue(IntegrationTestCase):
	def test_timed_task_is_overdue_after_its_time(self):
		due = rules("2026-10-23 10:00:00")
		self.assertTrue(due.is_overdue(task("2026-10-23 09:59:00")))
		self.assertFalse(due.is_overdue(task("2026-10-23 10:01:00")))

	def test_all_day_task_is_overdue_the_next_day(self):
		due = rules("2026-10-23 23:00:00")
		self.assertFalse(due.is_overdue(task("2026-10-23 00:00:00", all_day=1)))
		self.assertTrue(due.is_overdue(task("2026-10-22 00:00:00", all_day=1)))

	def test_all_day_task_follows_the_user_day_at_midnight(self):
		# 18:30 UTC is midnight in Asia/Kolkata
		before = rules("2026-10-23 18:29:59", user_zone="Asia/Kolkata")
		after = rules("2026-10-23 18:30:00", user_zone="Asia/Kolkata")
		all_day = task("2026-10-23 00:00:00", all_day=1)
		self.assertFalse(before.is_overdue(all_day))
		self.assertTrue(after.is_overdue(all_day))

	def test_all_day_task_waits_for_a_user_behind_system_time(self):
		due = rules("2026-10-24 02:00:00", user_zone="America/New_York")
		self.assertFalse(due.is_overdue(task("2026-10-23 00:00:00", all_day=1)))
		self.assertTrue(due.is_due_today(task("2026-10-23 00:00:00", all_day=1)))

	def test_timed_task_is_due_today_on_the_user_day(self):
		due = rules("2026-10-23 20:00:00", user_zone="Asia/Kolkata")
		self.assertTrue(due.is_due_today(task("2026-10-23 19:00:00")))
		self.assertFalse(due.is_due_today(task("2026-10-23 18:00:00")))
		self.assertTrue(due.is_due_today(task("2026-10-24 00:00:00", all_day=1)))

	def test_user_day_uses_system_time_of_stored_dates(self):
		due = rules("2026-10-23 20:00:00", user_zone="Asia/Kolkata", system_zone="Asia/Kolkata")
		self.assertTrue(due.is_due_today(task("2026-10-23 08:00:00")))
		self.assertFalse(due.is_overdue(task("2026-10-23 00:00:00", all_day=1)))

	def test_closed_or_undated_tasks_are_never_overdue(self):
		due = rules("2026-10-23 10:00:00")
		self.assertFalse(due.is_overdue(task("2026-10-01 10:00:00", status="Done")))
		self.assertFalse(due.is_overdue(task("2026-10-01 10:00:00", status="Canceled")))
		self.assertFalse(due.is_overdue(task(None)))
		self.assertFalse(due.is_due_today(task("2026-10-23 12:00:00", status="Done")))

	def test_overdue_condition_matches_is_overdue(self):
		due = rules("2026-10-23 18:30:00", user_zone="Asia/Kolkata")
		tasks = [
			make_task("2026-10-23 18:29:00"),
			make_task("2026-10-23 18:31:00"),
			make_task("2026-10-23 00:00:00", all_day=1),
			make_task("2026-10-24 00:00:00", all_day=1),
			make_task("2026-10-01 00:00:00", status="Done"),
		]
		expected = {t.name for t in tasks if due.is_overdue(t)}
		self.assertEqual(len(expected), 2)
		self.assertEqual(query_names(due.overdue_condition, tasks), expected)

	def test_due_by_today_condition_matches_overdue_or_due_today(self):
		due = rules("2026-10-23 20:00:00", user_zone="Asia/Kolkata")
		tasks = [
			make_task("2026-10-23 10:00:00"),
			make_task("2026-10-24 18:29:00"),
			make_task("2026-10-24 18:31:00"),
			make_task("2026-10-24 00:00:00", all_day=1),
			make_task("2026-10-25 00:00:00", all_day=1),
			make_task("2026-10-01 00:00:00", status="Done"),
		]
		expected = {t.name for t in tasks if due.is_overdue(t) or due.is_due_today(t)}
		self.assertEqual(len(expected), 3)
		self.assertEqual(query_names(due.due_by_today_condition, tasks), expected)

	def test_went_overdue_between_shifts_all_day_tasks_by_a_day(self):
		tasks = [
			make_task("2026-10-24 00:30:00"),
			make_task("2026-10-23 00:00:00", all_day=1),
			make_task("2026-10-24 00:00:00", all_day=1),
		]
		condition = partial(went_overdue_between, since="2026-10-24 00:00:00", until="2026-10-24 01:00:00")
		self.assertEqual(query_names(condition, tasks), {tasks[0].name, tasks[1].name})

	def test_all_day_task_keeps_only_its_day(self):
		all_day = make_task("2026-10-23 15:45:00", all_day=1)
		timed = make_task("2026-10-23 15:45:00")
		self.assertEqual(get_datetime(all_day.due_date), get_datetime("2026-10-23 00:00:00"))
		self.assertEqual(get_datetime(timed.due_date), get_datetime("2026-10-23 15:45:00"))

	def test_follow_up_is_an_open_task_linked_to_a_lead_or_deal(self):
		linked = {"reference_doctype": "CRM Lead", "reference_docname": "CRM-LEAD-1"}
		self.assertTrue(is_follow_up(task(None, **linked)))
		self.assertFalse(is_follow_up(task(None, status="Done", **linked)))
		self.assertFalse(is_follow_up(task(None, reference_doctype="Contact", reference_docname="x")))
		self.assertFalse(is_follow_up(task(None, reference_doctype=None, reference_docname=None)))


def make_task(due_date, **kwargs):
	return frappe.get_doc(
		{"doctype": "CRM Task", "title": "Call back", "due_date": due_date, **kwargs}
	).insert()


def query_names(condition, tasks):
	table = frappe.qb.DocType("CRM Task")
	names = [t.name for t in tasks]
	rows = frappe.qb.from_(table).select(table.name).where(table.name.isin(names) & condition(table)).run()
	return {row[0] for row in rows}
