import frappe
from frappe.utils import add_days, add_to_date, now_datetime, nowdate

from crm.api.home import get_widget_data
from crm.tests.test_home import AGENT, MANAGER, make_user
from crm.tests.test_home_widgets import HomeWidgetTestCase, names

OUTSIDER = "home.outsider@example.com"
BOSS = "home.boss@example.com"


class TeamWidgetTestCase(HomeWidgetTestCase):
	"""MANAGER heads a Sales Hierarchy subtree with AGENT under them. OUTSIDER is outside
	that subtree and BOSS is a Sales Manager outside the hierarchy, so BOSS sees everyone."""

	def setUp(self):
		super().setUp()
		make_user(OUTSIDER, "Sales User")
		make_user(BOSS, "Sales User", "Sales Manager")
		frappe.db.set_single_value("FCRM Settings", "enable_sales_hierarchy", 1)
		frappe.db.delete("CRM Sales Hierarchy", {"user": ["in", [AGENT, MANAGER, OUTSIDER, BOSS]]})
		head = hierarchy_node(MANAGER, is_group=1)
		hierarchy_node(AGENT, reports_to=head)
		hierarchy_node(OUTSIDER)

	def team(self, widget, user=MANAGER, doctype="Both"):
		return get_widget_data(widget, doctype, user)


class TestTeamScope(TeamWidgetTestCase):
	def test_manager_in_the_hierarchy_sees_their_subtree(self):
		mine = self.lead(lead_owner=MANAGER, awaiting_reply_since=now_datetime())
		reports = self.lead(awaiting_reply_since=now_datetime())
		self.lead(lead_owner=OUTSIDER, awaiting_reply_since=now_datetime())
		self.assertEqual(set(names(self.team("team_replies_waiting"))), {mine, reports})

	def test_manager_outside_the_hierarchy_and_system_manager_see_everyone(self):
		long_ago = add_to_date(now_datetime(), years=-20)
		leads = {
			self.lead(awaiting_reply_since=long_ago),
			self.lead(lead_owner=OUTSIDER, awaiting_reply_since=long_ago),
		}
		for user in (BOSS, "Administrator"):
			self.assertTrue(leads <= set(names(self.team("team_replies_waiting", user))))

	def test_agents_cannot_load_team_widgets(self):
		with self.assertRaises(frappe.PermissionError):
			self.team("team_replies_waiting", AGENT)


class TestTeamRepliesWaiting(TeamWidgetTestCase):
	def test_oldest_wait_first_with_owner(self):
		newer = self.lead(awaiting_reply_since=add_to_date(now_datetime(), hours=-1))
		older = self.deal(deal_owner=MANAGER, awaiting_reply_since=add_to_date(now_datetime(), hours=-3))
		rows = self.team("team_replies_waiting")["rows"]
		self.assertEqual([(row["name"], row["owner"]) for row in rows], [(older, MANAGER), (newer, AGENT)])

	def test_assignee_stands_in_for_a_missing_owner(self):
		lead = self.lead(awaiting_reply_since=now_datetime())
		frappe.db.set_value("CRM Lead", lead, "lead_owner", None)
		self.assertEqual(self.team("team_replies_waiting")["rows"][0]["owner"], AGENT)


class TestTeamOverdueFollowUps(TeamWidgetTestCase):
	def test_team_follow_ups_overdue_in_the_last_30_days_with_owner(self):
		mine = self.follow_up(add_days(now_datetime(), -2), assigned_to=MANAGER)
		reports = self.follow_up(add_days(nowdate(), -30), all_day=1)
		self.follow_up(add_days(nowdate(), -31), all_day=1)
		self.follow_up(nowdate(), all_day=1)
		self.follow_up(add_days(now_datetime(), -1), assigned_to=OUTSIDER)
		self.follow_up(add_days(now_datetime(), -1), status="Done")

		rows = self.team("team_overdue_follow_ups")["rows"]
		self.assertEqual(
			[(row["name"], row["assigned_to"]) for row in rows], [(reports, AGENT), (mine, MANAGER)]
		)

	def test_manager_outside_the_hierarchy_sees_every_sales_user(self):
		before = self.team("team_overdue_follow_ups", BOSS)["total"]
		self.follow_up(add_days(now_datetime(), -1), assigned_to=OUTSIDER)
		self.assertEqual(self.team("team_overdue_follow_ups", BOSS)["total"], before + 1)


def hierarchy_node(user, **kwargs):
	return frappe.get_doc({"doctype": "CRM Sales Hierarchy", "user": user, **kwargs}).insert().name
