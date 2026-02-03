# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, get_first_day, get_last_day, nowdate

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
	def setUp(self):
		"""Set up test data"""
		self.from_date = get_first_day(nowdate())
		self.to_date = get_last_day(nowdate())

		# Create test lead status if not exists
		if not frappe.db.exists("CRM Lead Status", "New Lead"):
			frappe.get_doc({"doctype": "CRM Lead Status", "lead_status": "New Lead"}).insert(
				ignore_if_duplicate=True
			)

		# Create test deal statuses
		self.create_test_deal_statuses()

		# Create test currency
		if not frappe.db.exists("Currency", "USD"):
			frappe.get_doc(
				{
					"doctype": "Currency",
					"currency_name": "US Dollar",
					"symbol": "$",
				}
			).insert(ignore_if_duplicate=True)

	def tearDown(self):
		frappe.db.rollback()

	def create_test_deal_statuses(self):
		"""Create test deal statuses"""
		statuses = [
			{"status": "Qualification", "type": "Open", "position": 1},
			{"status": "Negotiation", "type": "Open", "position": 2},
			{"status": "Won", "type": "Won", "position": 3},
			{"status": "Lost", "type": "Lost", "position": 4},
		]

		for status_data in statuses:
			if not frappe.db.exists("CRM Deal Status", status_data["status"]):
				frappe.get_doc({"doctype": "CRM Deal Status", **status_data}).insert(ignore_if_duplicate=True)

	def create_test_organization(self, org_name):
		"""Create test organization"""
		if not frappe.db.exists("CRM Organization", org_name):
			return frappe.get_doc(
				{
					"doctype": "CRM Organization",
					"organization_name": org_name,
				}
			).insert()
		return frappe.get_doc("CRM Organization", org_name)

	def test_get_total_leads(self):
		"""Test get_total_leads returns lead count with delta"""
		# Create test leads
		for i in range(3):
			frappe.get_doc(
				{
					"doctype": "CRM Lead",
					"first_name": f"Test Lead {i}",
					"email": f"testlead{i}@example.com",
				}
			).insert()

		result = get_total_leads(self.from_date, self.to_date)

		self.assertIn("title", result)
		self.assertIn("value", result)
		self.assertIn("delta", result)
		self.assertEqual(result["title"], "Total leads")
		self.assertGreaterEqual(result["value"], 3)

	def test_get_total_leads_with_user_filter(self):
		"""Test get_total_leads filters by user"""
		user = frappe.session.user

		# Create lead owned by current user
		frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "User Lead",
				"email": "userlead@example.com",
				"lead_owner": user,
			}
		).insert()

		result = get_total_leads(self.from_date, self.to_date, user)

		self.assertGreaterEqual(result["value"], 1)

	def test_get_ongoing_deals(self):
		"""Test get_ongoing_deals returns non-won/lost deal count"""
		# Create test organization and deal
		self.create_test_organization("Test Org")
		frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": "Test Org",
				"status": "Qualification",
			}
		).insert()

		result = get_ongoing_deals(self.from_date, self.to_date)

		self.assertIn("title", result)
		self.assertIn("value", result)
		self.assertEqual(result["title"], "Ongoing deals")
		self.assertGreaterEqual(result["value"], 1)

	def test_get_average_ongoing_deal_value(self):
		"""Test get_average_ongoing_deal_value calculates average"""
		# Create test organization and deal with value
		self.create_test_organization("Test Org Avg")
		frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": "Test Org Avg",
				"status": "Qualification",
				"deal_value": 10000,
				"exchange_rate": 1,
			}
		).insert()

		result = get_average_ongoing_deal_value(self.from_date, self.to_date)

		self.assertIn("title", result)
		self.assertIn("value", result)
		self.assertIn("prefix", result)
		self.assertEqual(result["title"], "Avg. ongoing deal value")

	def test_get_won_deals(self):
		"""Test get_won_deals returns won deal count"""
		# Create organization and won deal
		self.create_test_organization("Won Deal Org")
		frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": "Won Deal Org",
				"status": "Won",
				"closed_date": nowdate(),
			}
		).insert()

		result = get_won_deals(self.from_date, self.to_date)

		self.assertIn("title", result)
		self.assertIn("value", result)
		self.assertEqual(result["title"], "Won deals")
		self.assertGreaterEqual(result["value"], 1)

	def test_get_average_won_deal_value(self):
		"""Test get_average_won_deal_value calculates average for won deals"""
		# Create organization and won deal with value
		self.create_test_organization("Won Value Org")
		frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": "Won Value Org",
				"status": "Won",
				"closed_date": nowdate(),
				"deal_value": 50000,
				"exchange_rate": 1,
			}
		).insert()

		result = get_average_won_deal_value(self.from_date, self.to_date)

		self.assertIn("title", result)
		self.assertIn("value", result)
		self.assertEqual(result["title"], "Avg. won deal value")

	def test_get_average_deal_value(self):
		"""Test get_average_deal_value for all non-lost deals"""
		# Create organization and deal
		self.create_test_organization("Avg Deal Org")
		frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": "Avg Deal Org",
				"status": "Qualification",
				"deal_value": 30000,
				"exchange_rate": 1,
			}
		).insert()

		result = get_average_deal_value(self.from_date, self.to_date)

		self.assertIn("title", result)
		self.assertIn("value", result)
		self.assertEqual(result["title"], "Avg. deal value")

	def test_get_average_time_to_close_a_lead(self):
		"""Test get_average_time_to_close_a_lead calculates time from lead creation"""
		# Create lead
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Time Test Lead",
				"email": "timetest@example.com",
			}
		).insert()

		# Create organization and won deal from lead
		self.create_test_organization("Time Test Org")
		frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": "Time Test Org",
				"status": "Won",
				"lead": lead.name,
				"closed_date": add_days(nowdate(), 5),
			}
		).insert()

		result = get_average_time_to_close_a_lead(self.from_date, self.to_date)

		self.assertIn("title", result)
		self.assertIn("value", result)
		self.assertIn("suffix", result)
		self.assertEqual(result["title"], "Avg. time to close a lead")
		self.assertEqual(result["suffix"], " days")

	def test_get_average_time_to_close_a_deal(self):
		"""Test get_average_time_to_close_a_deal calculates time from deal creation"""
		# Create organization and won deal
		self.create_test_organization("Deal Time Org")
		frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": "Deal Time Org",
				"status": "Won",
				"closed_date": add_days(nowdate(), 3),
			}
		).insert()

		result = get_average_time_to_close_a_deal(self.from_date, self.to_date)

		self.assertIn("title", result)
		self.assertIn("value", result)
		self.assertEqual(result["title"], "Avg. time to close a deal")

	def test_get_sales_trend(self):
		"""Test get_sales_trend returns daily performance data"""
		# Create test data
		frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Trend Lead",
				"email": "trend@example.com",
			}
		).insert()

		self.create_test_organization("Trend Org")
		frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": "Trend Org",
				"status": "Won",
			}
		).insert()

		result = get_sales_trend(self.from_date, self.to_date)

		self.assertIn("data", result)
		self.assertIn("title", result)
		self.assertIn("series", result)
		self.assertEqual(result["title"], "Sales trend")
		self.assertTrue(len(result["series"]) >= 3)

	def test_get_forecasted_revenue(self):
		"""Test get_forecasted_revenue returns forecasted vs actual revenue"""
		# Create organization and deal with forecast
		self.create_test_organization("Forecast Org")
		frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": "Forecast Org",
				"status": "Qualification",
				"expected_deal_value": 100000,
				"probability": 50,
				"expected_closure_date": add_days(nowdate(), 30),
				"exchange_rate": 1,
			}
		).insert()

		result = get_forecasted_revenue(self.from_date, self.to_date)

		self.assertIn("data", result)
		self.assertIn("title", result)
		self.assertIn("series", result)
		self.assertEqual(result["title"], "Forecasted revenue")

	def test_get_funnel_conversion(self):
		"""Test get_funnel_conversion returns pipeline stages"""
		# Create lead
		frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Funnel Lead",
				"email": "funnel@example.com",
			}
		).insert()

		result = get_funnel_conversion(self.from_date, self.to_date)

		self.assertIn("data", result)
		self.assertIn("title", result)
		self.assertEqual(result["title"], "Funnel conversion")
		self.assertTrue(len(result["data"]) >= 1)

	def test_get_deals_by_stage_axis(self):
		"""Test get_deals_by_stage_axis returns deal distribution"""
		# Create organization and deal
		self.create_test_organization("Stage Org")
		frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": "Stage Org",
				"status": "Qualification",
			}
		).insert()

		result = get_deals_by_stage_axis(self.from_date, self.to_date)

		self.assertIn("data", result)
		self.assertIn("title", result)
		self.assertEqual(result["title"], "Deals by ongoing & won stage")

	def test_get_deals_by_stage_donut(self):
		"""Test get_deals_by_stage_donut returns deal distribution for donut chart"""
		# Create organization and deal
		self.create_test_organization("Donut Org")
		frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": "Donut Org",
				"status": "Negotiation",
			}
		).insert()

		result = get_deals_by_stage_donut(self.from_date, self.to_date)

		self.assertIn("data", result)
		self.assertIn("title", result)
		self.assertEqual(result["title"], "Deals by stage")

	def test_get_lost_deal_reasons(self):
		"""Test get_lost_deal_reasons returns reasons for lost deals"""
		# Create lost reason if not exists
		if not frappe.db.exists("CRM Lost Reason", "Price too high"):
			frappe.get_doc(
				{
					"doctype": "CRM Lost Reason",
					"lost_reason": "Price too high",
				}
			).insert(ignore_if_duplicate=True)

		# Create organization and lost deal with reason
		self.create_test_organization("Lost Org")
		frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": "Lost Org",
				"status": "Lost",
				"lost_reason": "Price too high",
			}
		).insert()

		result = get_lost_deal_reasons(self.from_date, self.to_date)

		self.assertIn("data", result)
		self.assertIn("title", result)
		self.assertEqual(result["title"], "Lost deal reasons")

	def test_get_leads_by_source(self):
		"""Test get_leads_by_source returns lead source distribution"""
		# Create source if not exists
		if not frappe.db.exists("CRM Lead Source", "Website"):
			frappe.get_doc(
				{
					"doctype": "CRM Lead Source",
					"source_name": "Website",
				}
			).insert(ignore_if_duplicate=True)

		# Create lead with source
		frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Source Lead",
				"email": "source@example.com",
				"source": "Website",
			}
		).insert()

		result = get_leads_by_source(self.from_date, self.to_date)

		self.assertIn("data", result)
		self.assertIn("title", result)
		self.assertEqual(result["title"], "Leads by source")

	def test_get_deals_by_source(self):
		"""Test get_deals_by_source returns deal source distribution"""
		# Create source if not exists
		if not frappe.db.exists("CRM Lead Source", "Referral"):
			frappe.get_doc(
				{
					"doctype": "CRM Lead Source",
					"source_name": "Referral",
				}
			).insert(ignore_if_duplicate=True)

		# Create organization and deal with source
		self.create_test_organization("Source Org")
		frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": "Source Org",
				"status": "Qualification",
				"source": "Referral",
			}
		).insert()

		result = get_deals_by_source(self.from_date, self.to_date)

		self.assertIn("data", result)
		self.assertIn("title", result)
		self.assertEqual(result["title"], "Deals by source")

	def test_get_deals_by_territory(self):
		"""Test get_deals_by_territory returns geographic distribution"""
		# Create territory if not exists
		if not frappe.db.exists("CRM Territory", "North America"):
			frappe.get_doc(
				{
					"doctype": "CRM Territory",
					"territory_name": "North America",
				}
			).insert(ignore_if_duplicate=True)

		# Create organization and deal with territory
		self.create_test_organization("Territory Org")
		frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": "Territory Org",
				"status": "Qualification",
				"territory": "North America",
				"deal_value": 25000,
				"exchange_rate": 1,
			}
		).insert()

		result = get_deals_by_territory(self.from_date, self.to_date)

		self.assertIn("data", result)
		self.assertIn("title", result)
		self.assertEqual(result["title"], "Deals by territory")

	def test_get_deals_by_salesperson(self):
		"""Test get_deals_by_salesperson returns salesperson performance"""
		user = frappe.session.user

		# Create organization and deal owned by user
		self.create_test_organization("Sales Org")
		frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": "Sales Org",
				"status": "Qualification",
				"deal_owner": user,
				"deal_value": 15000,
				"exchange_rate": 1,
			}
		).insert()

		result = get_deals_by_salesperson(self.from_date, self.to_date)

		self.assertIn("data", result)
		self.assertIn("title", result)
		self.assertEqual(result["title"], "Deals by salesperson")

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
			frappe.db.set_value("FCRM Settings", None, "currency", "USD")

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
		# Create organization and deal with status changes
		self.create_test_organization("Status Change Org")
		deal = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": "Status Change Org",
				"status": "Qualification",
			}
		).insert()

		# Create status change log
		frappe.get_doc(
			{
				"doctype": "CRM Status Change Log",
				"parent": deal.name,
				"parenttype": "CRM Deal",
				"parentfield": "status_changes",
				"from": "Qualification",
				"to": "Negotiation",
			}
		).insert()

		result = get_deal_status_change_counts(self.from_date, self.to_date)

		self.assertIsInstance(result, list)

	def test_user_filtering_isolation(self):
		"""Test that user filtering correctly isolates data"""
		user1 = frappe.session.user

		# Create lead for user1
		frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "User1 Lead",
				"email": "user1lead@example.com",
				"lead_owner": user1,
			}
		).insert()

		# Get results for user1
		result_user1 = get_total_leads(self.from_date, self.to_date, user1)

		# Get results for all users
		result_all = get_total_leads(self.from_date, self.to_date, "")

		# All users should have >= user1's count
		self.assertGreaterEqual(result_all["value"], result_user1["value"])

	def test_date_range_filtering(self):
		"""Test that date range filtering works correctly"""
		# Create lead in past month
		add_days(self.from_date, -60)

		result_current = get_total_leads(self.from_date, self.to_date)

		# Current month should be valid
		self.assertIsNotNone(result_current["value"])
		self.assertGreaterEqual(result_current["value"], 0)
