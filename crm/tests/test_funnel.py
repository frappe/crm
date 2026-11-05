import frappe
from frappe.utils import add_days, getdate

from crm.api.dashboard import get_funnel_conversion
from crm.api.home import get_widget_data
from crm.tests.test_home import AGENT, MANAGER
from crm.tests.test_home_widgets import HomeWidgetTestCase, status


class TestFunnelConversion(HomeWidgetTestCase):
	def setUp(self):
		super().setUp()
		self.lost = status("CRM Deal Status", "Lost")
		self.stages = frappe.get_all(
			"CRM Deal Status",
			filters={"type": ["in", ("Open", "Ongoing", "Won")]},
			order_by="position asc",
			pluck="name",
		)

	def funnel(self, user=AGENT):
		today = getdate()
		rows = get_funnel_conversion(add_days(today, -29), today, user)["data"]
		return {row["stage"]: row["count"] for row in rows}

	def moved_deal(self, *statuses, **kwargs):
		deal = frappe.get_doc("CRM Deal", self.deal(status=statuses[0], **kwargs))
		deal.flags.ignore_mandatory = True
		for next_status in statuses[1:]:
			deal.status = next_status
			if frappe.db.get_value("CRM Deal Status", next_status, "type") == "Lost":
				deal.lost_reason, deal.lost_notes = "Other", "Went quiet"
			deal.save()
		return deal.name

	def test_counts_each_deal_up_to_the_furthest_stage_it_reached(self):
		first, second, *_, won = self.stages
		self.moved_deal(first)
		self.moved_deal(first, won)
		self.moved_deal(first, second, self.lost)

		funnel = self.funnel()
		self.assertEqual(funnel[first], 3, "the stage a deal was created in counts")
		self.assertEqual(funnel[second], 2, "a lost deal counts up to where it got")
		self.assertEqual(funnel[self.stages[-2]], 1, "a deal that skipped a stage still passed it")
		self.assertEqual(funnel[won], 1)

	def test_lists_every_pipeline_stage_in_order(self):
		self.lead()
		self.assertEqual(list(self.funnel()), ["Leads", *self.stages])

	def test_owner_counts_only_their_records(self):
		self.lead()
		self.lead(lead_owner=MANAGER)
		self.moved_deal(self.stages[0], self.stages[1])
		self.moved_deal(self.stages[0], self.stages[1], deal_owner=MANAGER)

		funnel = self.funnel()
		self.assertEqual(funnel["Leads"], 1)
		self.assertEqual(funnel[self.stages[1]], 1)


class TestFunnelWidget(HomeWidgetTestCase):
	def widget(self, user=AGENT, period=None):
		rows = get_widget_data("funnel_conversion", user=user, period=period)["rows"]
		return {row["stage"]: row["count"] for row in rows}

	def test_agent_sees_own_records_over_the_period(self):
		self.lead()
		old = self.lead()
		frappe.db.set_value("CRM Lead", old, "creation", add_days(getdate(), -20))
		self.lead(lead_owner=MANAGER)

		self.assertEqual(self.widget()["Leads"], 2)
		self.assertEqual(self.widget(period="last_week")["Leads"], 1)

	def test_is_empty_without_records(self):
		self.assertEqual(get_widget_data("funnel_conversion", user=AGENT)["rows"], [])
