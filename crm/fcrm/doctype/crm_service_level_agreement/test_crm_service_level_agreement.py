# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from datetime import datetime, time

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, get_datetime, now_datetime


class TestCRMServiceLevelAgreement(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_sla_creation(self):
		"""Test creating a basic SLA"""
		sla = create_test_sla(sla_name="Test SLA", apply_on="CRM Lead")

		self.assertEqual(sla.sla_name, "Test SLA")
		self.assertEqual(sla.apply_on, "CRM Lead")
		self.assertTrue(sla.enabled)

	def test_validate_default_sla(self):
		"""Test that only one default SLA can exist per doctype"""
		# Create first default SLA
		create_test_sla(sla_name="Default SLA 1", apply_on="CRM Lead", default=True)

		# Try to create another default SLA for same doctype
		sla2 = frappe.get_doc(
			{
				"doctype": "CRM Service Level Agreement",
				"sla_name": "Default SLA 2",
				"apply_on": "CRM Lead",
				"default": True,
				"enabled": True,
			}
		)

		with self.assertRaises(frappe.ValidationError):
			sla2.insert()

	def test_validate_condition_valid(self):
		"""Test that valid condition passes validation"""
		sla = create_test_sla(
			sla_name="Conditional SLA",
			apply_on="CRM Lead",
			condition="doc.lead_owner == 'Administrator'",
		)

		# Should not raise error
		self.assertTrue(sla.name)

	def test_validate_condition_invalid(self):
		"""Test that invalid condition fails validation"""
		sla = frappe.get_doc(
			{
				"doctype": "CRM Service Level Agreement",
				"sla_name": "Invalid Condition SLA",
				"apply_on": "CRM Lead",
				"enabled": True,
				"condition": "invalid python code here!!!",
			}
		)

		with self.assertRaises(frappe.ValidationError):
			sla.insert()

	def test_get_priorities(self):
		"""Test get_priorities returns dict with priority as key"""
		sla = create_test_sla_with_priorities()

		priorities = sla.get_priorities()

		self.assertIsInstance(priorities, dict)
		self.assertIn("High", priorities)
		self.assertIn("Medium", priorities)
		self.assertEqual(priorities["High"].first_response_time, 3600)
		self.assertEqual(priorities["Medium"].first_response_time, 7200)

	def test_get_default_priority(self):
		"""Test get_default_priority returns the default priority"""
		sla = create_test_sla_with_priorities()

		default_priority = sla.get_default_priority()

		self.assertEqual(default_priority, "Medium")

	def test_get_workdays(self):
		"""Test get_workdays returns dict with workday as key"""
		sla = create_test_sla_with_working_hours()

		workdays = sla.get_workdays()

		self.assertIsInstance(workdays, dict)
		self.assertIn("Monday", workdays)
		self.assertIn("Tuesday", workdays)
		self.assertEqual(workdays["Monday"].start_time, time(9, 0))
		self.assertEqual(workdays["Monday"].end_time, time(17, 0))

	def test_get_working_days(self):
		"""Test get_working_days returns list of working days"""
		sla = create_test_sla_with_working_hours()

		working_days = sla.get_working_days()

		self.assertIsInstance(working_days, list)
		self.assertIn("Monday", working_days)
		self.assertIn("Tuesday", working_days)
		self.assertIn("Wednesday", working_days)

	def test_get_working_hours(self):
		"""Test get_working_hours returns dict with time tuples"""
		sla = create_test_sla_with_working_hours()

		working_hours = sla.get_working_hours()

		self.assertIsInstance(working_hours, dict)
		self.assertIn("Monday", working_hours)
		start_time, end_time = working_hours["Monday"]
		self.assertEqual(start_time, time(9, 0))
		self.assertEqual(end_time, time(17, 0))

	def test_is_working_time(self):
		"""Test is_working_time checks if datetime is within working hours"""
		sla = create_test_sla_with_working_hours()
		working_hours = sla.get_working_hours()

		# Monday 10 AM - should be working time
		monday_10am = datetime(2024, 1, 1, 10, 0, 0)  # Monday
		self.assertTrue(sla.is_working_time(monday_10am, working_hours))

		# Monday 8 AM - before working hours
		monday_8am = datetime(2024, 1, 1, 8, 0, 0)
		self.assertFalse(sla.is_working_time(monday_8am, working_hours))

		# Monday 6 PM - after working hours
		monday_6pm = datetime(2024, 1, 1, 18, 0, 0)
		self.assertFalse(sla.is_working_time(monday_6pm, working_hours))

	def test_get_holidays(self):
		"""Test get_holidays returns list of holiday dates"""
		# Create holiday list
		holiday_list = create_test_holiday_list()

		sla = create_test_sla_with_working_hours(holiday_list=holiday_list.name)

		holidays = sla.get_holidays()

		self.assertIsInstance(holidays, list)
		self.assertTrue(len(holidays) > 0)

	def test_handle_creation(self):
		"""Test handle_creation sets sla_creation timestamp"""
		sla = create_test_sla_with_priorities()

		# Create a CRM Lead document
		doc = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Test Handle Creation", "sla_creation": None}
		)

		before_time = now_datetime()
		sla.handle_creation(doc)
		after_time = now_datetime()

		# Verify timestamp is set and within reasonable time window
		self.assertIsNotNone(doc.sla_creation)
		self.assertGreaterEqual(doc.sla_creation, before_time)
		self.assertLessEqual(doc.sla_creation, after_time)

	def test_handle_creation_existing_timestamp(self):
		"""Test handle_creation doesn't override existing timestamp"""
		sla = create_test_sla_with_priorities()

		existing_time = get_datetime("2024-01-01 10:00:00")
		doc = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Test Existing Timestamp", "sla_creation": existing_time}
		)

		sla.handle_creation(doc)

		self.assertEqual(doc.sla_creation, existing_time)

	def test_set_first_responded_on(self):
		"""Test set_first_responded_on sets response timestamps"""
		sla = create_test_sla_with_priorities()

		doc = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test First Response",
				"communication_status": "High",
				"first_responded_on": None,
				"last_responded_on": None,
			}
		)

		sla.set_first_responded_on(doc)

		self.assertIsNotNone(doc.first_responded_on)
		self.assertIsNotNone(doc.last_responded_on)

	def test_set_first_responded_on_default_priority(self):
		"""Test set_first_responded_on doesn't set for default priority"""
		sla = create_test_sla_with_priorities()

		doc = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test Default Priority",
				"communication_status": "Medium",  # Default priority
				"first_responded_on": None,
				"last_responded_on": None,
			}
		)

		sla.set_first_responded_on(doc)

		self.assertIsNone(doc.first_responded_on)

	def test_set_response_by(self):
		"""Test set_response_by calculates response deadline"""
		sla = create_test_sla_with_priorities()

		start_time = get_datetime("2024-01-01 10:00:00")  # Monday 10 AM
		doc = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test Response By",
				"sla_creation": start_time,
				"communication_status": "High",
				"response_by": None,
			}
		)

		sla.set_response_by(doc)

		# High priority has 3600 seconds (1 hour) response time
		# Response by should be 1 hour after creation (11:00 AM)
		self.assertIsNotNone(doc.response_by)
		expected_response = get_datetime("2024-01-01 11:00:00")
		self.assertEqual(doc.response_by, expected_response)

	def test_set_response_by_existing(self):
		"""Test set_response_by doesn't override existing response_by"""
		sla = create_test_sla_with_priorities()

		existing_response = get_datetime("2024-01-01 15:00:00")
		doc = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test Response By Existing",
				"sla_creation": get_datetime("2024-01-01 10:00:00"),
				"communication_status": "High",
				"response_by": existing_response,
			}
		)

		sla.set_response_by(doc)

		self.assertEqual(doc.response_by, existing_response)

	def test_is_first_response_failed_before_deadline(self):
		"""Test is_first_response_failed when response is before deadline"""
		sla = create_test_sla_with_priorities()

		doc = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test Response Before Deadline",
				"response_by": add_to_date(now_datetime(), hours=1),
				"first_responded_on": now_datetime(),
			}
		)

		self.assertFalse(sla.is_first_response_failed(doc))

	def test_is_first_response_failed_after_deadline(self):
		"""Test is_first_response_failed when response is after deadline"""
		sla = create_test_sla_with_priorities()

		doc = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test Response After Deadline",
				"response_by": add_to_date(now_datetime(), hours=-1),
				"first_responded_on": now_datetime(),
			}
		)

		self.assertTrue(sla.is_first_response_failed(doc))

	def test_is_first_response_failed_no_response(self):
		"""Test is_first_response_failed when no response yet but deadline passed"""
		sla = create_test_sla_with_priorities()

		doc = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test No Response",
				"response_by": add_to_date(now_datetime(), hours=-1),
				"first_responded_on": None,
			}
		)

		self.assertTrue(sla.is_first_response_failed(doc))

	def test_handle_sla_status_fulfilled(self):
		"""Test handle_sla_status sets status to Fulfilled"""
		sla = create_test_sla_with_priorities()

		doc = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test SLA Fulfilled",
				"response_by": add_to_date(now_datetime(), hours=1),
				"first_responded_on": now_datetime(),
				"sla_status": None,
			}
		)

		sla.handle_sla_status(doc)

		self.assertEqual(doc.sla_status, "Fulfilled")

	def test_handle_sla_status_first_response_due(self):
		"""Test handle_sla_status sets status to First Response Due"""
		sla = create_test_sla_with_priorities()

		doc = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test First Response Due",
				"response_by": add_to_date(now_datetime(), hours=1),
				"first_responded_on": None,
				"sla_status": None,
			}
		)

		sla.handle_sla_status(doc)

		self.assertEqual(doc.sla_status, "First Response Due")

	def test_handle_sla_status_failed(self):
		"""Test handle_sla_status sets status to Failed"""
		sla = create_test_sla_with_priorities()

		doc = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test SLA Failed",
				"response_by": add_to_date(now_datetime(), hours=-1),
				"first_responded_on": now_datetime(),
				"sla_status": None,
			}
		)

		sla.handle_sla_status(doc)

		self.assertEqual(doc.sla_status, "Failed")

	def test_calc_time_basic(self):
		"""Test calc_time calculates end time correctly"""
		sla = create_test_sla_with_working_hours()

		start_time = get_datetime("2024-01-01 10:00:00")  # Monday 10 AM
		duration_seconds = 3600  # 1 hour

		end_time = sla.calc_time(start_time, duration_seconds)

		# Should be 11 AM on same day
		self.assertEqual(end_time.hour, 11)
		self.assertEqual(end_time.day, 1)

	def test_calc_time_crosses_day(self):
		"""Test calc_time when duration crosses to next day"""
		sla = create_test_sla_with_working_hours()

		start_time = get_datetime("2024-01-01 16:00:00")  # Monday 4 PM
		duration_seconds = 7200  # 2 hours (work ends at 5 PM)

		end_time = sla.calc_time(start_time, duration_seconds)

		# Should be Tuesday morning
		self.assertEqual(end_time.day, 2)

	def test_calc_elapsed_time_same_day(self):
		"""Test calc_elapsed_time within same working day"""
		sla = create_test_sla_with_working_hours()

		start_time = get_datetime("2024-01-01 10:00:00")  # Monday 10 AM
		end_time = get_datetime("2024-01-01 12:00:00")  # Monday 12 PM

		elapsed = sla.calc_elapsed_time(start_time, end_time)

		# Should be 2 hours = 7200 seconds
		self.assertEqual(elapsed, 7200)

	def test_set_rolling_responses_first_entry(self):
		"""Test set_rolling_responses creates first entry"""
		sla = create_test_sla_with_priorities(rolling_responses=True)

		# Create a proper CRM Lead document (don't insert to avoid triggering SLA application)
		doc = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Rolling Response Test",
				"email": "rolling@example.com",
			}
		)

		# Set required fields for rolling responses
		doc.rolling_responses = []
		doc.last_response_time = 100
		doc.last_responded_on = now_datetime()
		doc.response_by = add_to_date(now_datetime(), hours=1)
		doc.first_responded_on = now_datetime()

		sla.set_rolling_responses(doc)

		self.assertEqual(len(doc.rolling_responses), 1)
		self.assertEqual(doc.rolling_responses[0].response_time, 100)
		# Response before deadline (response_by is 1 hour in future) should be Fulfilled
		self.assertEqual(doc.rolling_responses[0].status, "Fulfilled")

	def test_handle_rolling_sla_status(self):
		"""Test handle_rolling_sla_status sets rolling SLA status"""
		sla = create_test_sla_with_priorities(rolling_responses=True)

		doc = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test Rolling SLA",
				"response_by": add_to_date(now_datetime(), hours=1),
				"last_responded_on": now_datetime(),
				"communication_status": "High",
				"sla_status": None,
			}
		)
		doc.append("rolling_responses", {"status": "Fulfilled"})

		sla.handle_rolling_sla_status(doc)

		self.assertIn(doc.sla_status, ["Fulfilled", "Rolling Response Due", "Failed"])

	def test_set_rolling_responses_subsequent_entry(self):
		"""Test set_rolling_responses creates subsequent entries with consistent timestamps"""
		sla = create_test_sla_with_priorities(rolling_responses=True)

		doc = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Rolling Response Subsequent",
				"email": "rolling_sub@example.com",
			}
		)

		# Set up as if first response already happened
		doc.rolling_responses = []
		first_response_time = now_datetime()
		doc.last_response_time = 100
		doc.last_responded_on = add_to_date(first_response_time, hours=-1)
		doc.response_by = add_to_date(first_response_time, hours=1)
		doc.first_responded_on = add_to_date(first_response_time, hours=-1)
		doc.communication_status = "High"  # Non-default = agent responding

		# Add first entry
		doc.append(
			"rolling_responses",
			{"status": "Fulfilled", "response_time": 100, "responded_on": doc.last_responded_on},
		)

		sla.set_rolling_responses(doc)

		self.assertEqual(len(doc.rolling_responses), 2)
		# responded_on and last_responded_on should be exactly the same (no race condition)
		self.assertEqual(doc.rolling_responses[1].responded_on, doc.last_responded_on)

	def test_calc_elapsed_time_excludes_holidays(self):
		"""Test calc_elapsed_time excludes holidays from elapsed time"""
		holiday_list = create_test_holiday_list()
		sla = create_test_sla_with_working_hours(holiday_list=holiday_list.name)

		# Start on Friday Jan 12, end on Tuesday Jan 16 (Jan 15 is a holiday)
		start_time = get_datetime("2024-01-12 10:00:00")  # Friday 10 AM
		end_time = get_datetime("2024-01-16 12:00:00")  # Tuesday 12 PM

		elapsed = sla.calc_elapsed_time(start_time, end_time)

		# Friday: 10 AM - 5 PM = 7 hours = 25200s
		# Sat/Sun: not working days
		# Monday Jan 15: holiday — should be excluded
		# Tuesday: 9 AM - 12 PM = 3 hours = 10800s
		# Total = 25200 + 10800 = 36000s
		self.assertEqual(elapsed, 36000)

	def test_handle_rolling_sla_status_failed_takes_priority(self):
		"""Test that Failed status takes priority over Fulfilled in rolling SLA"""
		sla = create_test_sla_with_priorities(rolling_responses=True)

		doc = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test Rolling Failed Priority",
				"response_by": add_to_date(now_datetime(), hours=-1),  # Deadline already passed
				"last_responded_on": now_datetime(),  # Responded after deadline
				"communication_status": "High",  # Non-default priority
				"sla_status": None,
			}
		)
		doc.append("rolling_responses", {"status": "Fulfilled"})

		sla.handle_rolling_sla_status(doc)

		# Even though communication_status != default, Failed should take priority
		self.assertEqual(doc.sla_status, "Failed")

	def test_handle_rolling_sla_status_fulfilled(self):
		"""Test that Fulfilled is set when response is before deadline"""
		sla = create_test_sla_with_priorities(rolling_responses=True)

		doc = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test Rolling Fulfilled",
				"response_by": add_to_date(now_datetime(), hours=1),  # Deadline in future
				"last_responded_on": now_datetime(),
				"communication_status": "High",  # Non-default
				"sla_status": None,
			}
		)
		doc.append("rolling_responses", {"status": "Fulfilled"})

		sla.handle_rolling_sla_status(doc)

		self.assertEqual(doc.sla_status, "Fulfilled")

	def test_handle_rolling_sla_status_rolling_response_due(self):
		"""Test that Rolling Response Due is set when status is default priority"""
		sla = create_test_sla_with_priorities(rolling_responses=True)

		doc = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test Rolling Due",
				"response_by": add_to_date(now_datetime(), hours=1),  # Not expired
				"last_responded_on": now_datetime(),
				"communication_status": "Medium",  # Default priority
				"sla_status": None,
			}
		)
		doc.append("rolling_responses", {"status": "Fulfilled"})

		sla.handle_rolling_sla_status(doc)

		self.assertEqual(doc.sla_status, "Rolling Response Due")

	def test_set_rolling_responses_does_not_update_response_by(self):
		"""Test that set_rolling_responses does NOT update response_by when agent replies.
		response_by should only be updated when a customer message arrives (via handle_targets)."""
		sla = create_test_sla_with_priorities(rolling_responses=True)

		doc = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test Response By No Update",
			}
		)

		doc.rolling_responses = []
		doc.last_response_time = 100
		doc.last_responded_on = add_to_date(now_datetime(), hours=-1)
		doc.response_by = add_to_date(now_datetime(), hours=1)  # Deadline in the future
		doc.first_responded_on = add_to_date(now_datetime(), hours=-1)
		doc.communication_status = "High"  # Non-default = agent responding

		# Add first entry
		doc.append(
			"rolling_responses",
			{"status": "Fulfilled", "response_time": 100, "responded_on": doc.last_responded_on},
		)

		old_response_by = doc.response_by
		sla.set_rolling_responses(doc)

		# response_by should NOT have been changed by set_rolling_responses
		self.assertEqual(doc.response_by, old_response_by)

	def test_rolling_response_correct_with_customer_reply_gap(self):
		"""Test the exact scenario from the bug report:
		Agent responds on time, customer replies days later, agent responds again.
		The second response should be evaluated against a deadline set from when
		the customer message arrived, NOT from the agent's first response."""
		sla = create_test_sla_with_priorities(rolling_responses=True)

		doc = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test Customer Reply Gap",
			}
		)

		# Simulate: agent responded 1 hour ago, response_by set to future (via handle_targets)
		doc.rolling_responses = []
		doc.last_response_time = 100
		doc.last_responded_on = add_to_date(now_datetime(), hours=-1)
		doc.first_responded_on = doc.last_responded_on
		doc.response_by = add_to_date(now_datetime(), hours=1)  # Valid future deadline
		doc.communication_status = "High"  # Non-default = agent responding

		# First rolling response entry (fulfilled)
		doc.append(
			"rolling_responses",
			{"status": "Fulfilled", "response_time": 100, "responded_on": doc.last_responded_on},
		)

		# Agent replies again — response_by is in the future, so this should be Fulfilled
		sla.set_rolling_responses(doc)

		self.assertEqual(len(doc.rolling_responses), 2)
		self.assertEqual(doc.rolling_responses[1].status, "Fulfilled")

	def test_set_rolling_responses_stale_deadline_marks_failed(self):
		"""Test that when response_by is a stale past deadline (from a previous cycle),
		the agent's response is correctly marked as Failed."""
		sla = create_test_sla_with_priorities(rolling_responses=True)

		doc = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test Stale Deadline Failed",
			}
		)

		doc.rolling_responses = []
		doc.last_response_time = 100
		doc.last_responded_on = add_to_date(now_datetime(), hours=-1)
		doc.first_responded_on = doc.last_responded_on
		# Stale response_by from a previous cycle (already expired)
		doc.response_by = add_to_date(now_datetime(), hours=-2)
		doc.communication_status = "High"  # Non-default = agent responding

		# First entry from earlier cycle
		doc.append(
			"rolling_responses",
			{"status": "Fulfilled", "response_time": 100, "responded_on": doc.last_responded_on},
		)

		sla.set_rolling_responses(doc)

		self.assertEqual(len(doc.rolling_responses), 2)
		# Agent replied AFTER the stale deadline -> should be Failed
		self.assertEqual(doc.rolling_responses[1].status, "Failed")

	def test_is_rolling_response_failed_waiting_for_agent(self):
		"""Test is_rolling_response_failed when waiting for agent response (default priority).
		Should check response_by against now_datetime(), not last_responded_on."""
		sla = create_test_sla_with_priorities(rolling_responses=True)

		# Deadline has passed but agent hasn't responded yet
		doc = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test Waiting For Agent",
				"response_by": add_to_date(now_datetime(), hours=-1),  # Expired
				"last_responded_on": add_to_date(now_datetime(), hours=-3),  # Agent's previous reply
				"communication_status": "Medium",  # Default priority = waiting for agent
			}
		)

		self.assertTrue(sla.is_rolling_response_failed(doc))

	def test_is_rolling_response_failed_waiting_for_agent_not_expired(self):
		"""Test is_rolling_response_failed when waiting for agent and deadline hasn't passed."""
		sla = create_test_sla_with_priorities(rolling_responses=True)

		doc = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test Waiting Not Expired",
				"response_by": add_to_date(now_datetime(), hours=1),  # Not expired
				"last_responded_on": add_to_date(now_datetime(), hours=-3),
				"communication_status": "Medium",  # Default priority
			}
		)

		self.assertFalse(sla.is_rolling_response_failed(doc))

	def test_apply_method_full_workflow(self):
		"""Test apply method executes full SLA workflow"""
		sla = create_test_sla_with_priorities()

		# Create a CRM Lead document
		doc = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test Apply Full Workflow",
				"communication_status": "High",
				"sla_creation": None,
				"first_responded_on": None,
				"last_responded_on": None,
				"response_by": None,
				"sla_status": None,
			}
		)

		# Mock has_value_changed to return False (new document)
		doc.has_value_changed = lambda x: False
		doc.is_new = lambda: True

		sla.apply(doc)

		# Verify SLA was applied
		self.assertIsNotNone(doc.sla_creation)
		self.assertIsNotNone(doc.response_by)
		self.assertIsNotNone(doc.sla_status)


def create_test_sla(**kwargs):
	"""Helper function to create a CRM Service Level Agreement for testing"""
	data = {
		"doctype": "CRM Service Level Agreement",
		"sla_name": "Test SLA",
		"apply_on": "CRM Lead",
		"enabled": True,
		"default": False,
	}

	data.update(kwargs)

	sla = frappe.get_doc(data)

	# Add minimum required priorities if not provided
	if not sla.get("priorities"):
		# Ensure we have a communication status to reference
		if not frappe.db.exists("CRM Communication Status", "Medium"):
			frappe.get_doc(
				{
					"doctype": "CRM Communication Status",
					"status": "Medium",
				}
			).insert(ignore_if_duplicate=True)

		sla.append(
			"priorities",
			{
				"priority": "Medium",
				"default_priority": True,
				"first_response_time": 3600,
			},
		)

	# Add minimum required working hours if not provided
	if not sla.get("working_hours"):
		sla.append(
			"working_hours",
			{
				"workday": "Monday",
				"start_time": time(9, 0),
				"end_time": time(17, 0),
			},
		)

	sla.insert()
	return sla


def create_test_sla_with_priorities(**kwargs):
	"""Helper to create SLA with priority levels"""
	rolling_responses = kwargs.pop("rolling_responses", False)

	# Ensure communication statuses exist
	for priority_name in ["High", "Medium", "Low"]:
		if not frappe.db.exists("CRM Communication Status", priority_name):
			frappe.get_doc(
				{
					"doctype": "CRM Communication Status",
					"status": priority_name,
				}
			).insert(ignore_if_duplicate=True)

	sla = frappe.get_doc(
		{
			"doctype": "CRM Service Level Agreement",
			"sla_name": kwargs.get("sla_name", "SLA with Priorities"),
			"apply_on": kwargs.get("apply_on", "CRM Lead"),
			"enabled": True,
			"default": kwargs.get("default", False),
			"rolling_responses": rolling_responses,
		}
	)

	# Add priorities
	sla.append(
		"priorities",
		{
			"priority": "High",
			"default_priority": False,
			"first_response_time": 3600,  # 1 hour
		},
	)
	sla.append(
		"priorities",
		{
			"priority": "Medium",
			"default_priority": True,
			"first_response_time": 7200,  # 2 hours
		},
	)

	# Add working hours if specified
	if kwargs.get("add_working_hours", True):
		for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
			sla.append(
				"working_hours",
				{
					"workday": day,
					"start_time": time(9, 0),
					"end_time": time(17, 0),
				},
			)

	sla.insert()
	return sla


def create_test_sla_with_working_hours(**kwargs):
	"""Helper to create SLA with working hours"""
	# Ensure communication status exists
	if not frappe.db.exists("CRM Communication Status", "Medium"):
		frappe.get_doc(
			{
				"doctype": "CRM Communication Status",
				"status": "Medium",
			}
		).insert(ignore_if_duplicate=True)

	sla = frappe.get_doc(
		{
			"doctype": "CRM Service Level Agreement",
			"sla_name": kwargs.get("sla_name", "SLA with Working Hours"),
			"apply_on": kwargs.get("apply_on", "CRM Lead"),
			"enabled": True,
			"holiday_list": kwargs.get("holiday_list"),
		}
	)

	# Add working hours (Monday to Friday, 9 AM to 5 PM)
	for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
		sla.append(
			"working_hours",
			{
				"workday": day,
				"start_time": time(9, 0),
				"end_time": time(17, 0),
			},
		)

	# Add a default priority
	sla.append(
		"priorities",
		{
			"priority": "Medium",
			"default_priority": True,
			"first_response_time": 3600,
		},
	)

	sla.insert()
	return sla


def create_test_holiday_list():
	"""Helper to create a holiday list for testing"""
	from datetime import date

	holiday_list = frappe.get_doc(
		{
			"doctype": "CRM Holiday List",
			"holiday_list_name": "Test Holidays",
			"from_date": date(2024, 1, 1),
			"to_date": date(2024, 12, 31),
		}
	)

	# Add a sample holiday
	holiday_list.append("holidays", {"date": date(2024, 1, 15), "description": "Test Holiday"})

	holiday_list.insert()
	return holiday_list
