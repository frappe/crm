from unittest.mock import patch

import frappe
from frappe.utils import add_days, add_to_date, now_datetime, nowdate

from crm.api.home import get_widget_data
from crm.fcrm.doctype.crm_dashboard import team_widgets
from crm.fcrm.doctype.crm_dashboard.home_widgets import NoNextStep, RepliesWaiting
from crm.tests.test_home import AGENT, MANAGER, make_deal, make_lead, make_user
from crm.tests.test_home_widgets import HomeWidgetTestCase, names, status

OUTSIDER = "home.outsider@example.com"
BOSS = "home.boss@example.com"
OTHER_MANAGER = "home.manager2@example.com"


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


class TestUnassigned(TeamWidgetTestCase):
	def unassigned(self, **kwargs):
		return make_lead(**{"status": self.open_lead, **kwargs})

	def test_new_records_without_an_assignee_newest_first(self):
		older = self.unassigned()
		frappe.db.set_value("CRM Lead", older, "creation", add_days(now_datetime(), -1))
		newer = self.unassigned()
		deal = make_deal(status=status("CRM Deal Status", "Open"))
		self.lead()
		self.unassigned(status=self.ongoing_lead)
		self.unassigned(converted=1)

		rows = names(self.team("unassigned", BOSS))
		self.assertEqual(rows[: rows.index(older) + 1], [deal, newer, older])
		self.assertNotIn(deal, names(self.team("unassigned", BOSS, "Lead")))

	def test_count_stops_at_the_cap(self):
		def team_lead_without_assignee():
			frappe.db.set_value("CRM Lead", self.lead(), "_assign", None)

		with patch.object(team_widgets, "UNASSIGNED_CAP", 2):
			team_lead_without_assignee()
			team_lead_without_assignee()
			self.assertEqual(self.summary(), (2, False))
			team_lead_without_assignee()
			self.assertEqual(self.summary(), (2, True))

	def summary(self):
		data = self.team("unassigned")
		return data["total"], data["more"]


class TestTeamOverview(TeamWidgetTestCase):
	def setUp(self):
		super().setUp()
		self.clear_cache()

	def tearDown(self):
		self.clear_cache()
		super().tearDown()

	def clear_cache(self):
		for scope in (MANAGER, OTHER_MANAGER, "all"):
			frappe.cache.delete_value(overview_key(scope))

	def overview(self, user=MANAGER):
		return {row["user"]: row for row in self.team("team_overview", user)["rows"]}

	def test_counts_per_member_match_their_own_widgets(self):
		self.lead(awaiting_reply_since=now_datetime())
		idle = self.lead()
		frappe.db.set_value(
			"CRM Lead", idle, "modified", add_days(now_datetime(), -10), update_modified=False
		)
		self.follow_up(add_days(now_datetime(), -1))
		for seconds in (600, 1200):
			responded = self.lead(status=self.closed_lead)
			frappe.db.set_value("CRM Lead", responded, "first_response_time", seconds)
		self.deal(deal_owner=MANAGER)

		overview = self.overview()
		self.assertEqual(set(overview), {MANAGER, AGENT})
		self.assertEqual(
			overview[AGENT],
			{
				"user": AGENT,
				"open": 3,
				"replies_waiting": 1,
				"no_next_step": 1,
				"overdue_follow_ups": 1,
				"first_response_time": 900,
			},
		)
		self.assertEqual(overview[AGENT]["replies_waiting"], self.data(RepliesWaiting)["total"])
		self.assertEqual(overview[AGENT]["no_next_step"], self.data(NoNextStep)["total"])
		self.assertEqual(overview[MANAGER]["open"], 1)

	def test_cached_per_scope_for_a_few_minutes(self):
		make_user(OTHER_MANAGER, "Sales User", "Sales Manager")
		frappe.db.delete("CRM Sales Hierarchy", {"user": ["in", [OTHER_MANAGER, OUTSIDER]]})
		hierarchy_node(OUTSIDER, reports_to=hierarchy_node(OTHER_MANAGER, is_group=1))

		self.assertEqual(self.overview()[AGENT]["open"], 0)
		self.lead()
		self.assertEqual(self.overview()[AGENT]["open"], 0)
		self.assertEqual(set(self.overview(OTHER_MANAGER)), {OTHER_MANAGER, OUTSIDER})
		self.assertEqual(self.overview(BOSS)[AGENT]["open"], 1)

		ttl = frappe.cache.ttl(frappe.cache.make_key(overview_key(MANAGER)))
		self.assertTrue(120 <= ttl <= 300)


def overview_key(scope):
	return f"crm:home:team_overview:{scope}"


def hierarchy_node(user, **kwargs):
	return frappe.get_doc({"doctype": "CRM Sales Hierarchy", "user": user, **kwargs}).insert().name
