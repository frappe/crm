# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import json
import os

import frappe
from frappe.tests import IntegrationTestCase
from frappe.tests.utils import make_test_records
from frappe.utils import get_first_day, get_last_day, nowdate

from crm.api.dashboard import (
	get_average_deal_value,
	get_average_ongoing_deal_value,
	get_average_time_to_close_a_deal,
	get_average_time_to_close_a_lead,
	get_average_won_deal_value,
	get_base_currency_symbol,
	get_chart,
	get_dashboard,
	get_deal_status_change_counts,
	get_deals_by_salesperson,
	get_deals_by_source,
	get_deals_by_stage_axis,
	get_deals_by_stage_donut,
	get_deals_by_territory,
	get_forecasted_revenue,
	get_funnel_conversion,
	get_leads_by_source,
	get_lost_deal_reasons,
	get_ongoing_deals,
	get_sales_trend,
	get_total_leads,
	get_won_deals,
)


class TestDashboard(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		"""Set up test records once for all tests"""
		super().setUpClass()

		# Mark timestamp before creating test data
		cls.test_start_time = frappe.utils.now()

		# Load CRM user test records from crm/tests/test_records.json
		cls.load_crm_user_test_records()

		cls.from_date = get_first_day(nowdate())
		cls.to_date = get_last_day(nowdate())
		cls.user = "crm.manager@example.com"  # CRM manager from test_records.json
		cls.user2_email = "crm.user1@example.com"  # Test user from test_records.json

		# Load test records from test_records.json files in dependency order
		make_test_records("CRM Lead Status")
		make_test_records("CRM Deal Status")
		make_test_records("CRM Lead Source")
		make_test_records("CRM Lost Reason")
		make_test_records("CRM Organization")  # Load organizations before deals
		make_test_records("CRM Lead")
		make_test_records("CRM Deal")

	@classmethod
	def tearDownClass(cls):
		"""Clean up test records after all tests"""
		frappe.db.rollback()
		super().tearDownClass()

	@classmethod
	def load_crm_user_test_records(cls):
		"""Load CRM user test records from crm/tests/test_records.json"""
		test_records_path = os.path.join(os.path.dirname(__file__), "test_records.json")

		if os.path.exists(test_records_path):
			with open(test_records_path) as f:
				test_records = json.load(f)

			for record in test_records:
				if not frappe.db.exists("User", record.get("email")):
					doc = frappe.get_doc(record)
					doc.insert(ignore_permissions=True, ignore_if_duplicate=True)

	def test_get_total_leads(self):
		"""Test get_total_leads returns lead count with delta"""
		result = get_total_leads(self.from_date, self.to_date)

		self.assertIn("title", result)
		self.assertIn("value", result)
		self.assertIn("delta", result)
		self.assertEqual(result["title"], "Total leads")
		self.assertEqual(result["value"], 35)  # 35 leads from test_records.json

		# Test with user filter - crm.user1@example.com owns 3 leads
		result_user = get_total_leads(self.from_date, self.to_date, self.user2_email)
		self.assertEqual(result_user["value"], 3)
		self.assertLessEqual(result_user["value"], result["value"])

	def test_get_ongoing_deals(self):
		"""Test get_ongoing_deals returns non-won/lost deal count"""
		result = get_ongoing_deals(self.from_date, self.to_date)

		self.assertIn("title", result)
		self.assertIn("value", result)
		self.assertEqual(result["title"], "Ongoing deals")
		self.assertEqual(result["value"], 21)  # 21 ongoing deals (13 Qualification + 8 Negotiation)

		# Test with user filter - crm.user1@example.com owns 2 ongoing deals
		result_user = get_ongoing_deals(self.from_date, self.to_date, self.user2_email)
		self.assertEqual(result_user["value"], 2)
		self.assertLessEqual(result_user["value"], result["value"])

	def test_get_average_ongoing_deal_value(self):
		"""Test get_average_ongoing_deal_value calculates average"""
		# Test without user filter - filters by creation date within range
		result = get_average_ongoing_deal_value(self.from_date, self.to_date)

		self.assertIn("title", result)
		self.assertIn("value", result)
		self.assertIn("prefix", result)
		self.assertEqual(result["title"], "Avg. ongoing deal value")
		self.assertGreaterEqual(result["value"], 0)  # Average of ongoing deals created in current month

		# Test with user filter
		result_user = get_average_ongoing_deal_value(self.from_date, self.to_date, self.user2_email)
		self.assertGreaterEqual(result_user["value"], 0)

	def test_get_won_deals(self):
		"""Test get_won_deals returns won deal count"""
		result = get_won_deals(self.from_date, self.to_date)

		self.assertIn("title", result)
		self.assertIn("value", result)
		self.assertEqual(result["title"], "Won deals")
		self.assertEqual(result["value"], 8)  # 8 won deals from test_records.json

		# Test with user filter - crm.user1@example.com owns 0 won deals
		result_user = get_won_deals(self.from_date, self.to_date, self.user2_email)
		self.assertEqual(result_user["value"], 0)
		self.assertLessEqual(result_user["value"], result["value"])

	def test_get_average_won_deal_value(self):
		"""Test get_average_won_deal_value calculates average for won deals"""
		# Test without user filter - filters by closed_date within range
		result = get_average_won_deal_value(self.from_date, self.to_date)

		self.assertIn("title", result)
		self.assertIn("value", result)
		self.assertEqual(result["title"], "Avg. won deal value")
		self.assertGreaterEqual(result["value"], 0)  # Average of won deals closed in current month

		# Test with user filter
		result_user = get_average_won_deal_value(self.from_date, self.to_date, self.user2_email)
		self.assertGreaterEqual(result_user["value"], 0)

	def test_get_average_deal_value(self):
		"""Test get_average_deal_value for all non-lost deals"""
		# Test without user filter - filters by creation date within range
		result = get_average_deal_value(self.from_date, self.to_date)

		self.assertIn("title", result)
		self.assertIn("value", result)
		self.assertEqual(result["title"], "Avg. deal value")
		self.assertGreaterEqual(result["value"], 0)  # Average of non-lost deals created in current month

		# Test with user filter
		result_user = get_average_deal_value(self.from_date, self.to_date, self.user2_email)
		self.assertGreaterEqual(result_user["value"], 0)

	def test_get_average_time_to_close_a_lead(self):
		"""Test get_average_time_to_close_a_lead calculates time from lead creation"""
		# Test without user filter
		result = get_average_time_to_close_a_lead(self.from_date, self.to_date)

		self.assertIn("title", result)
		self.assertIn("value", result)
		self.assertIn("suffix", result)
		self.assertEqual(result["title"], "Avg. time to close a lead")
		self.assertEqual(result["suffix"], " days")
		self.assertEqual(result["value"], 0)  # Test records created on same day

		# Test with user filter
		result_user = get_average_time_to_close_a_lead(self.from_date, self.to_date, self.user2_email)
		self.assertEqual(result_user["value"], 0)  # Test records created on same day

	def test_get_average_time_to_close_a_deal(self):
		"""Test get_average_time_to_close_a_deal calculates time from deal creation"""
		# Test without user filter
		result = get_average_time_to_close_a_deal(self.from_date, self.to_date)

		self.assertIn("title", result)
		self.assertIn("value", result)
		self.assertEqual(result["title"], "Avg. time to close a deal")
		self.assertEqual(result["value"], 0)  # Test records created on same day

		# Test with user filter
		result_user = get_average_time_to_close_a_deal(self.from_date, self.to_date, self.user2_email)
		self.assertEqual(result_user["value"], 0)  # Test records created on same day

	def test_get_sales_trend(self):
		"""Test get_sales_trend returns daily performance data"""
		# Test without user filter
		result = get_sales_trend(self.from_date, self.to_date)

		self.assertIn("data", result)
		self.assertIn("title", result)
		self.assertIn("series", result)
		self.assertEqual(result["title"], "Sales trend")
		self.assertEqual(len(result["series"]), 3)  # leads, deals, won_deals
		self.assertEqual(result["series"][0]["name"], "leads")
		self.assertEqual(result["series"][1]["name"], "deals")
		self.assertEqual(result["series"][2]["name"], "won_deals")

		# Test with user filter
		result_user = get_sales_trend(self.from_date, self.to_date, self.user2_email)
		self.assertIn("data", result_user)
		self.assertEqual(len(result_user["series"]), 3)

	def test_get_forecasted_revenue(self):
		"""Test get_forecasted_revenue returns forecasted vs actual revenue"""
		# Test without user filter
		result = get_forecasted_revenue(self.from_date, self.to_date)

		self.assertIn("data", result)
		self.assertIn("title", result)
		self.assertIn("series", result)
		self.assertEqual(result["title"], "Forecasted revenue")

		# Test with user filter
		result_user = get_forecasted_revenue(self.from_date, self.to_date, self.user2_email)
		self.assertIn("data", result_user)
		self.assertIn("series", result_user)

	def test_get_funnel_conversion(self):
		"""Test get_funnel_conversion returns pipeline stages"""
		result = get_funnel_conversion(self.from_date, self.to_date)

		self.assertIn("data", result)
		self.assertIn("title", result)
		self.assertEqual(result["title"], "Funnel conversion")
		self.assertGreater(len(result["data"]), 0)
		self.assertEqual(result["data"][0]["stage"], "Leads")
		self.assertEqual(result["data"][0]["count"], 35)  # 35 leads from test_records.json

		# Test with user filter - crm.user1@example.com owns 3 leads
		result_user = get_funnel_conversion(self.from_date, self.to_date, self.user2_email)
		self.assertIn("data", result_user)
		self.assertGreater(len(result_user["data"]), 0)
		self.assertEqual(result_user["data"][0]["stage"], "Leads")
		self.assertEqual(result_user["data"][0]["count"], 3)

	def test_get_deals_by_stage_axis(self):
		"""Test get_deals_by_stage_axis returns deal distribution"""
		# Test without user filter
		result = get_deals_by_stage_axis(self.from_date, self.to_date)

		self.assertIn("data", result)
		self.assertIn("title", result)
		self.assertEqual(result["title"], "Deals by ongoing & won stage")

		# Test with user filter
		result_user = get_deals_by_stage_axis(self.from_date, self.to_date, self.user2_email)
		self.assertIn("data", result_user)

	def test_get_deals_by_stage_donut(self):
		"""Test get_deals_by_stage_donut returns deal distribution for donut chart"""
		# Test without user filter
		result = get_deals_by_stage_donut(self.from_date, self.to_date)

		self.assertIn("data", result)
		self.assertIn("title", result)
		self.assertEqual(result["title"], "Deals by stage")

		# Test with user filter
		result_user = get_deals_by_stage_donut(self.from_date, self.to_date, self.user2_email)
		self.assertIn("data", result_user)

	def test_get_lost_deal_reasons(self):
		"""Test get_lost_deal_reasons returns reasons for lost deals"""
		# Test without user filter
		result = get_lost_deal_reasons(self.from_date, self.to_date)

		self.assertIn("data", result)
		self.assertIn("title", result)
		self.assertEqual(result["title"], "Lost deal reasons")

		# Test with user filter
		result_user = get_lost_deal_reasons(self.from_date, self.to_date, self.user2_email)
		self.assertIn("data", result_user)

	def test_get_leads_by_source(self):
		"""Test get_leads_by_source returns lead source distribution"""
		# Test without user filter
		result = get_leads_by_source(self.from_date, self.to_date)

		self.assertIn("data", result)
		self.assertIn("title", result)
		self.assertEqual(result["title"], "Leads by source")

		# Test with user filter
		result_user = get_leads_by_source(self.from_date, self.to_date, self.user2_email)
		self.assertIn("data", result_user)

	def test_get_deals_by_source(self):
		"""Test get_deals_by_source returns deal source distribution"""
		# Test without user filter
		result = get_deals_by_source(self.from_date, self.to_date)

		self.assertIn("data", result)
		self.assertIn("title", result)
		self.assertEqual(result["title"], "Deals by source")

		# Test with user filter
		result_user = get_deals_by_source(self.from_date, self.to_date, self.user2_email)
		self.assertIn("data", result_user)

	def test_get_deals_by_territory(self):
		"""Test get_deals_by_territory returns geographic distribution"""
		# Test without user filter
		result = get_deals_by_territory(self.from_date, self.to_date)

		self.assertIn("data", result)
		self.assertIn("title", result)
		self.assertEqual(result["title"], "Deals by territory")

		# Test with user filter
		result_user = get_deals_by_territory(self.from_date, self.to_date, self.user2_email)
		self.assertIn("data", result_user)

	def test_get_deals_by_salesperson(self):
		"""Test get_deals_by_salesperson returns salesperson performance"""
		# Test without user filter
		result = get_deals_by_salesperson(self.from_date, self.to_date)

		self.assertIn("data", result)
		self.assertIn("title", result)
		self.assertEqual(result["title"], "Deals by salesperson")

		# Test with user filter
		result_user = get_deals_by_salesperson(self.from_date, self.to_date, self.user2_email)
		self.assertIn("data", result_user)

	def test_get_base_currency_symbol(self):
		"""Test get_base_currency_symbol returns currency symbol"""
		# Set USD as base currency
		if not frappe.db.exists("FCRM Settings"):
			frappe.get_doc(
				{
					"doctype": "FCRM Settings",
					"currency": "USD",
				}
			).insert()
		else:
			frappe.db.set_single_value("FCRM Settings", "currency", "USD")

		symbol = get_base_currency_symbol()

		self.assertIsNotNone(symbol)
		self.assertIsInstance(symbol, str)

	def test_get_dashboard(self):
		"""Test get_dashboard returns layout with data"""
		result = get_dashboard(self.from_date, self.to_date)

		self.assertIsInstance(result, list)
		# Dashboard should have layout items
		for item in result:
			self.assertIn("name", item)

	def test_get_chart(self):
		"""Test get_chart returns chart data"""
		result = get_chart("total_leads", "number", self.from_date, self.to_date)

		self.assertIsInstance(result, dict)
		self.assertIn("title", result)
		self.assertIn("value", result)

	def test_get_chart_invalid_name(self):
		"""Test get_chart returns error for invalid chart name"""
		result = get_chart("invalid_chart_name", "number", self.from_date, self.to_date)

		self.assertIn("error", result)

	def test_get_deal_status_change_counts(self):
		"""Test get_deal_status_change_counts returns status changes"""
		# Test records have deals, status changes may or may not exist
		result = get_deal_status_change_counts(self.from_date, self.to_date)

		self.assertIsInstance(result, list)

	def test_user_filtering_isolation(self):
		"""Test that user filtering correctly isolates data"""
		result_crm_user = get_total_leads(self.from_date, self.to_date, self.user2_email)
		result_all = get_total_leads(self.from_date, self.to_date, "")

		self.assertEqual(result_crm_user["value"], 3)  # crm.user1@example.com owns 3 leads
		self.assertEqual(result_all["value"], 35)  # 35 total leads
		self.assertGreaterEqual(result_all["value"], result_crm_user["value"])

	def test_date_range_filtering(self):
		"""Test that date range filtering works correctly"""
		result_current = get_total_leads(self.from_date, self.to_date)

		self.assertIsNotNone(result_current["value"])
		self.assertGreater(result_current["value"], 0)  # Should have leads created
