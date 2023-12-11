# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from datetime import timedelta
from frappe.model.document import Document
from frappe.utils import (
	add_to_date,
	get_datetime,
	get_weekdays,
	getdate,
	now_datetime,
	time_diff_in_seconds,
)


class CRMServiceLevelAgreement(Document):
	def apply(self, doc: Document):
		self.handle_new(doc)
		self.handle_status(doc)
		self.handle_targets(doc)
		self.handle_sla_status(doc)

	def handle_new(self, doc: Document):
		if not doc.is_new():
			return
		creation = doc.sla_creation or now_datetime()
		doc.sla_creation = creation

	def handle_status(self, doc: Document):
		if doc.is_new() or not doc.has_value_changed("status"):
			return
		self.set_first_responded_on(doc)
		self.set_first_response_time(doc)

	def set_first_responded_on(self, doc: Document):
		if doc.status != self.get_default_priority():
			doc.first_responded_on = (
				doc.first_responded_on or now_datetime()
			)

	def set_first_response_time(self, doc: Document):
		start_at = doc.sla_creation
		end_at = doc.first_responded_on
		if not start_at or not end_at:
			return
		doc.first_response_time = self.calc_elapsed_time(start_at, end_at)

	def handle_targets(self, doc: Document):
		self.set_response_by(doc)

	def set_response_by(self, doc: Document):
		start_time = doc.sla_creation
		status = doc.status

		priorities = self.get_priorities()
		priority = priorities.get(status)
		if not priority or doc.response_by:
			return

		first_response_time = priority.get("first_response_time", 0)
		end_time = self.calc_time(start_time, first_response_time)
		if end_time:
			doc.response_by = end_time

	def handle_sla_status(self, doc: Document):
		is_failed = self.is_first_response_failed(doc)
		options = {
			"Fulfilled": True,
			"First Response Due": not doc.first_responded_on,
			"Failed": is_failed,
		}
		for status in options:
			if options[status]:
				doc.sla_status = status

	def is_first_response_failed(self, doc: Document):
		if not doc.first_responded_on:
			return get_datetime(doc.response_by) < now_datetime()
		return get_datetime(doc.response_by) < get_datetime(doc.first_responded_on)

	def calc_time(
		self,
		start_at: str,
		duration_seconds: int,
	):
		res = get_datetime(start_at)
		time_needed = duration_seconds
		holidays = []
		weekdays = get_weekdays()
		workdays = self.get_workdays()
		while time_needed:
			today = res
			today_day = getdate(today)
			today_weekday = weekdays[today.weekday()]
			is_workday = today_weekday in workdays
			is_holiday = today_day in holidays
			if is_holiday or not is_workday:
				res = add_to_date(res, days=1, as_datetime=True)
				continue
			today_workday = workdays[today_weekday]
			now_in_seconds = time_diff_in_seconds(today, today_day)
			start_time = max(today_workday.start_time.total_seconds(), now_in_seconds)
			till_start_time = max(start_time - now_in_seconds, 0)
			end_time = max(today_workday.end_time.total_seconds(), now_in_seconds)
			time_left = max(end_time - start_time, 0)
			if not time_left:
				res = getdate(add_to_date(res, days=1, as_datetime=True))
				continue
			time_taken = min(time_needed, time_left)
			time_needed -= time_taken
			time_required = till_start_time + time_taken
			res = add_to_date(res, seconds=time_required, as_datetime=True)
		return res

	def calc_elapsed_time(self, start_time, end_time) -> float:
		"""
		Get took from start to end, excluding non-working hours

		:param start_at: Date at which calculation starts
		:param end_at: Date at which calculation ends
		:return: Number of seconds
		"""
		start_time = get_datetime(start_time)
		end_time = get_datetime(end_time)
		holiday_list = []
		working_day_list = self.get_working_days()
		working_hours = self.get_working_hours()

		total_seconds = 0
		current_time = start_time

		while current_time < end_time:
			in_holiday_list = current_time.date() in holiday_list
			not_in_working_day_list = get_weekdays()[current_time.weekday()] not in working_day_list
			if in_holiday_list or not_in_working_day_list or not self.is_working_time(current_time, working_hours):
				current_time += timedelta(seconds=1)
				continue
			total_seconds += 1
			current_time += timedelta(seconds=1)

		return total_seconds

	def get_priorities(self):
		"""
		Return priorities related info as a dict. With `priority` as key
		"""
		res = {}
		for row in self.priorities:
			res[row.priority] = row
		return res

	def get_default_priority(self):
		"""
		Return default priority
		"""
		for row in self.priorities:
			if row.default_priority:
				return row.priority

		return self.priorities[0].priority

	def get_workdays(self) -> dict[str, dict]:
		"""
		Return workdays related info as a dict. With `workday` as key
		"""
		res = {}
		for row in self.working_hours:
			res[row.workday] = row
		return res

	def get_working_days(self) -> dict[str, dict]:
		workdays = []
		for row in self.working_hours:
			workdays.append(row.workday)
		return workdays

	def get_working_hours(self) -> dict[str, dict]:
		res = {}
		for row in self.working_hours:
			res[row.workday] = (row.start_time, row.end_time)
		return res

	def is_working_time(self, date_time, working_hours):
		day_of_week = get_weekdays()[date_time.weekday()]
		start_time, end_time = working_hours.get(day_of_week, (0, 0))
		date_time = timedelta(hours=date_time.hour, minutes=date_time.minute, seconds=date_time.second)
		return start_time <= date_time < end_time
