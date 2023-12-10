# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
from typing import Literal

# import frappe
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
		self.set_first_response_time(doc)

	def set_first_response_time(self, doc: Document):
		start_at = doc.sla_creation
		end_at = doc.first_responded_on
		if not start_at or not end_at:
			return
		doc.first_response_time = self.calc_elapsed_time(start_at, end_at)

	def handle_targets(self, doc: Document):
		self.set_response_by(doc)

	def set_response_by(self, doc: Document):
		start = doc.sla_creation
		doc.response_by = self.calc_time(start, doc.status, "first_response_time")

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
		priority: str,
		target: Literal["first_response_time"],
	):
		res = get_datetime(start_at)
		priority = self.get_priorities()[priority]
		time_needed = priority.get(target, 0)
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


	def calc_elapsed_time(self, start_at, end_at) -> float:
		"""
		Get took from start to end, excluding non-working hours

		:param start_at: Date at which calculation starts
		:param end_at: Date at which calculation ends
		:return: Number of seconds
		"""
		start_at = getdate(start_at)
		end_at = getdate(end_at)
		time_took = 0
		holidays = []
		weekdays = get_weekdays()
		workdays = self.get_workdays()
		while getdate(start_at) <= getdate(end_at):
			today = start_at
			today_day = getdate(today)
			today_weekday = weekdays[today.weekday()]
			is_workday = today_weekday in workdays
			is_holiday = today_day in holidays
			if is_holiday or not is_workday:
				start_at = getdate(add_to_date(start_at, days=1, as_datetime=True))
				continue
			today_workday = workdays[today_weekday]
			is_today = getdate(start_at) == getdate(end_at)
			if not is_today:
				working_start = today_workday.start_time
				working_end = today_workday.end_time
				working_time = time_diff_in_seconds(working_start, working_end)
				time_took += working_time
				start_at = getdate(add_to_date(start_at, days=1, as_datetime=True))
				continue
			now_in_seconds = time_diff_in_seconds(today, today_day)
			start_time = max(today_workday.start_time.total_seconds(), now_in_seconds)
			end_at_seconds = time_diff_in_seconds(getdate(end_at), end_at)
			end_time = max(today_workday.end_time.total_seconds(), end_at_seconds)
			time_taken = end_time - start_time
			time_took += time_taken
			start_at = getdate(add_to_date(start_at, days=1, as_datetime=True))
		return time_took

	def get_priorities(self):
		"""
		Return priorities related info as a dict. With `priority` as key
		"""
		res = {}
		for row in self.priorities:
			res[row.priority] = row
		return res

	def get_workdays(self) -> dict[str, dict]:
		"""
		Return workdays related info as a dict. With `workday` as key
		"""
		res = {}
		for row in self.working_hours:
			res[row.workday] = row
		return res
