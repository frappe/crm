import frappe
from frappe.utils import add_days, getdate, now_datetime

from crm.api.dashboard import get_forecasted_revenue
from crm.api.home import get_widget_data
from crm.tests.test_home import AGENT, MANAGER
from crm.tests.test_home_widgets import HomeWidgetTestCase, status


class SalesWidgetTestCase(HomeWidgetTestCase):
	def setUp(self):
		super().setUp()
		self.won = status("CRM Deal Status", "Won")
		self.lost = status("CRM Deal Status", "Lost")

	def deal(self, value=0, **kwargs):
		return super().deal(deal_value=value, exchange_rate=1, **kwargs)

	def closed(self, value, status, **kwargs):
		deal = frappe.get_doc("CRM Deal", self.deal(value, **kwargs))
		deal.flags.ignore_mandatory = True
		deal.status = status
		if status == self.lost:
			deal.lost_reason, deal.lost_notes = "Other", "Went quiet"
		deal.save()
		return deal

	def widget(self, name, user=AGENT):
		return get_widget_data(name, user=user)


class TestWon(SalesWidgetTestCase):
	def won_days_ago(self, value, days):
		deal = self.closed(value, self.won)
		frappe.db.set_value("CRM Deal", deal.name, "closed_date", add_days(getdate(), -days))

	def test_value_won_in_the_period_against_the_one_before(self):
		self.closed(300, self.won)
		self.closed(500, self.lost)
		self.won_days_ago(100, 40)
		self.won_days_ago(900, 70)

		data = self.widget("won_this_month")
		self.assertEqual(data["value"], 300)
		self.assertEqual(data["delta"], 200)
		self.assertEqual(len(data["sparkline"]), 30)
		self.assertEqual(data["sparkline"][-1], 300)

	def test_period_sets_the_window(self):
		self.closed(300, self.won)
		self.won_days_ago(100, 10)

		data = get_widget_data("won_this_month", user=AGENT, period="last_week")
		self.assertEqual(len(data["sparkline"]), 7)
		self.assertEqual(data["delta"], 200)

	def test_unknown_period_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			get_widget_data("won_this_month", user=AGENT, period="yesterday")


class TestExpectedRevenue(SalesWidgetTestCase):
	def setUp(self):
		super().setUp()
		frappe.db.set_single_value("FCRM Settings", "enable_forecasting", 1)
		self.probability = frappe.db.get_value("CRM Deal Status", self.open_deal, "probability") / 100

	def forecast(self, expected, **kwargs):
		return HomeWidgetTestCase.deal(
			self,
			expected_deal_value=expected,
			expected_closure_date=add_days(getdate(), 30),
			exchange_rate=1,
			**kwargs,
		)

	def entered_days_ago(self, deal: str, days: int):
		frappe.db.set_value(
			"CRM Status Change Log",
			{"parent": deal, "parenttype": "CRM Deal"},
			"from_date",
			add_days(now_datetime(), -days),
		)

	def test_needs_forecasting(self):
		frappe.db.set_single_value("FCRM Settings", "enable_forecasting", 0)
		self.assertEqual(self.widget("expected_revenue"), {"forecasting": False})

	def test_weights_expected_value_by_stage_probability(self):
		self.forecast(400)
		self.forecast(700, deal_owner=MANAGER)

		data = self.widget("expected_revenue")
		self.assertAlmostEqual(data["value"], 400 * self.probability)
		self.assertEqual(data["sparkline"][-1], data["value"])

	def test_compares_with_the_start_of_the_period(self):
		self.entered_days_ago(self.forecast(1000), 35)
		self.forecast(500)

		data = self.widget("expected_revenue")
		self.assertAlmostEqual(data["sparkline"][0], 1000 * self.probability)
		self.assertAlmostEqual(data["delta"], 50)

	def test_manager_counts_every_open_deal(self):
		before = self.widget("expected_revenue", MANAGER)["value"]
		self.forecast(400)
		self.forecast(700, deal_owner=MANAGER)
		after = self.widget("expected_revenue", MANAGER)["value"]
		self.assertAlmostEqual(after, before + 1100 * self.probability)


class TestTopOpenDeals(SalesWidgetTestCase):
	def test_biggest_open_deals_first(self):
		small = self.deal(100)
		big = self.deal(900)
		self.deal(0)
		self.closed(5000, self.won)

		rows = self.widget("top_open_deals")["rows"]
		self.assertEqual([row["name"] for row in rows], [big, small])


class TestForecast(SalesWidgetTestCase):
	def test_lost_deals_forecast_nothing(self):
		month = add_days(getdate(), 40)
		key = getdate(month).strftime("%Y-%m-01")
		lost = self.closed(0, self.lost, expected_closure_date=month)
		frappe.db.set_value("CRM Deal", lost.name, {"expected_deal_value": 1000, "probability": 50})

		rows = {row["month"]: row for row in get_forecasted_revenue(user=AGENT)["data"]}
		self.assertIn(key, rows)
		self.assertIn(rows[key]["forecasted"], ("", 0))
