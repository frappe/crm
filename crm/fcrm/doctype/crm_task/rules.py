# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""When a CRM Task is due and overdue.

A timed task's due_date is an instant in system time, so it is overdue once that instant
passes. An all-day task's due_date holds only its day, unshifted by any timezone, so it
stays on that day for every user and is overdue when the user's next day starts.
"""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import frappe
from frappe.utils import get_datetime, get_system_timezone, now_datetime

CLOSED_STATUSES = ("Done", "Canceled")
FOLLOW_UP_DOCTYPES = ("CRM Lead", "CRM Deal")


def is_follow_up(task) -> bool:
	return (
		task.status not in CLOSED_STATUSES
		and task.reference_doctype in FOLLOW_UP_DOCTYPES
		and bool(task.reference_docname)
	)


def went_overdue_between(task, since, until):
	"""Condition for open tasks that became overdue in [since, until], in system time."""
	since, until = get_datetime(since), get_datetime(until)
	one_day = timedelta(days=1)
	timed = (task.all_day == 0) & task.due_date[since:until]
	all_day = (task.all_day == 1) & task.due_date[since - one_day : until - one_day]
	return task.status.notin(CLOSED_STATUSES) & (timed | all_day)


class TaskDue:
	def __init__(self, user: str | None = None, now: datetime | None = None):
		self.system_zone = ZoneInfo(get_system_timezone())
		self.user_zone = ZoneInfo(_user_time_zone(user or frappe.session.user))
		self.now = now or now_datetime()
		self.today = self.now.replace(tzinfo=self.system_zone).astimezone(self.user_zone).date()

	def is_overdue(self, task) -> bool:
		if task.status in CLOSED_STATUSES or not task.due_date:
			return False
		due = get_datetime(task.due_date)
		if task.all_day:
			return due.date() < self.today
		return due < self.now

	def is_due_today(self, task) -> bool:
		if task.status in CLOSED_STATUSES or not task.due_date:
			return False
		due = get_datetime(task.due_date)
		if task.all_day:
			return due.date() == self.today
		return self._day_start(self.today) <= due < self._day_start(self.today + timedelta(days=1))

	def overdue_condition(self, task):
		"""Query condition for open overdue tasks, for `frappe.qb` on a CRM Task table."""
		timed = (task.all_day == 0) & (task.due_date < self.now)
		all_day = (task.all_day == 1) & (task.due_date < datetime.combine(self.today, time.min))
		return task.status.notin(CLOSED_STATUSES) & (timed | all_day)

	def _day_start(self, day: date) -> datetime:
		"""Midnight of the user's day, as a naive system time like stored datetimes."""
		start = datetime.combine(day, time.min, tzinfo=self.user_zone)
		return start.astimezone(self.system_zone).replace(tzinfo=None)


def _user_time_zone(user: str) -> str:
	return frappe.get_cached_value("User", user, "time_zone") or get_system_timezone()
