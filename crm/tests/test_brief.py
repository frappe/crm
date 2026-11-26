import frappe
from frappe.cache_manager import clear_defaults_cache
from frappe.desk.form.assign_to import add as assign
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, add_to_date, now_datetime, nowdate

from crm.api.home import get_tab_data, set_brief_doctype, set_brief_tab
from crm.fcrm.doctype.crm_dashboard.brief import (
	DOCTYPE_KEY,
	TAB_KEY,
	MineBrief,
	TeamBrief,
	allocate,
	get_brief,
	get_brief_count,
	get_brief_records,
)
from crm.tests.test_home import AGENT, MANAGER, make_lead, make_task
from crm.tests.test_home_widgets import HomeWidgetTestCase
from crm.tests.test_team_widgets import BOSS, TeamWidgetTestCase


def of_kind(brief, *kinds):
	return [item for item in brief["items"] if item["kind"] in kinds]


def kind_names(brief, *kinds):
	return [item.get("name") for item in of_kind(brief, *kinds)]


class TestAllocate(IntegrationTestCase):
	def test_each_group_gets_its_slots(self):
		rows = {"a": [1, 2, 3], "b": [1, 2, 3], "c": [1, 2]}
		shown = allocate(rows, {"a": 2, "b": 2, "c": 1})
		self.assertEqual({key: len(value) for key, value in shown.items()}, {"a": 2, "b": 2, "c": 1})

	def test_unused_slots_pass_to_other_groups(self):
		rows = {"a": [1, 2, 3, 4, 5, 6], "b": [], "c": [1]}
		shown = allocate(rows, {"a": 2, "b": 2, "c": 1})
		self.assertEqual({key: len(value) for key, value in shown.items()}, {"a": 4, "b": 0, "c": 1})

	def test_never_more_than_the_total_slots(self):
		rows = {"a": list(range(9)), "b": list(range(9))}
		shown = allocate(rows, {"a": 3, "b": 2})
		self.assertEqual(sum(len(value) for value in shown.values()), 5)


class TestMineBrief(HomeWidgetTestCase):
	def brief(self):
		return MineBrief(AGENT).summary()

	def idle(self, lead, days=10):
		frappe.db.set_value(
			"CRM Lead", lead, {"modified": add_days(now_datetime(), -days)}, update_modified=False
		)

	def idle_lead(self, days=10):
		lead = self.lead()
		self.idle(lead, days)
		frappe.db.set_value("ToDo", {"reference_name": lead}, "creation", add_days(now_datetime(), -days))
		return lead

	def contacted_lead(self):
		"""Not a new lead, so it adds no item of its own."""
		return self.lead(last_outbound_at=now_datetime())

	def test_a_quiet_day_has_no_groups(self):
		brief = self.brief()
		self.assertEqual(brief, {"items": [], "total": 0, "more": {}, "older": {}})

	def test_waiting_items_go_oldest_first(self):
		newer = self.lead(awaiting_reply_since=add_days(now_datetime(), -1))
		older = self.lead(awaiting_reply_since=add_days(now_datetime(), -9))
		self.assertEqual(kind_names(self.brief(), "waiting"), [older, newer])

	def test_never_more_than_five_items_but_the_total_counts_all(self):
		for _ in range(7):
			self.lead(awaiting_reply_since=now_datetime())
		brief = self.brief()
		self.assertEqual(len(brief["items"]), 5)
		self.assertEqual(brief["total"], 7)

	def test_links_to_the_waiting_records_it_has_no_room_for(self):
		leads = {self.lead(awaiting_reply_since=now_datetime()) for _ in range(7)}
		brief = self.brief()
		shown = set(kind_names(brief, "waiting"))
		self.assertEqual(set(brief["more"]["CRM Lead"]), leads - shown)

	def test_idle_records_are_not_linked(self):
		for _ in range(9):
			self.idle_lead()
		self.assertEqual(self.brief()["more"], {})

	def test_idle_records_count_only_when_there_is_room_to_show_them(self):
		for _ in range(9):
			self.idle_lead()
		brief = self.brief()
		self.assertEqual(len(of_kind(brief, "no_next_step")), 5)
		self.assertEqual(brief["total"], 5)

	def test_a_waiting_record_past_its_deadline_is_flagged(self):
		past = self.lead(
			awaiting_reply_since=now_datetime(),
			response_by=add_to_date(now_datetime(), hours=-1),
		)
		answered = self.lead(
			awaiting_reply_since=now_datetime(),
			response_by=add_to_date(now_datetime(), hours=-1),
			last_outbound_at=add_days(now_datetime(), -1),
		)
		flags = {item["name"]: item["past_response"] for item in of_kind(self.brief(), "waiting")}
		self.assertEqual(flags, {past: 1, answered: 0})

	def test_new_leads_share_one_row(self):
		leads = [make_lead(status=self.open_lead, lead_owner=MANAGER) for _ in range(2)]
		frappe.set_user(MANAGER)
		for lead in leads:
			assign({"assign_to": [AGENT], "doctype": "CRM Lead", "name": lead})
		frappe.set_user("Administrator")
		brief = self.brief()
		rows = of_kind(brief, "new")
		self.assertEqual([row["count"] for row in rows], [2])
		self.assertEqual(len(rows[0]["names"]), 2)
		self.assertEqual(brief["total"], 2)

	def test_overdue_follow_ups_come_before_records_with_no_next_step(self):
		self.idle_lead()
		linked = self.lead()
		make_task(
			add_days(nowdate(), -3),
			assigned_to=AGENT,
			reference_doctype="CRM Lead",
			reference_docname=linked,
		)
		kinds = [item["kind"] for item in of_kind(self.brief(), "follow_up", "no_next_step")]
		self.assertEqual(kinds, ["follow_up", "no_next_step"])

	def test_high_priority_follow_ups_come_first(self):
		def follow_up(days, priority):
			return make_task(
				add_days(nowdate(), days),
				assigned_to=AGENT,
				reference_doctype="CRM Lead",
				reference_docname=self.lead(),
				priority=priority,
			).name

		low_overdue = follow_up(-3, "Low")
		high_today = follow_up(0, "High")
		medium_overdue = follow_up(-1, "Medium")
		self.assertEqual(kind_names(self.brief(), "follow_up"), [high_today, low_overdue, medium_overdue])

	def test_a_new_lead_is_not_also_a_no_next_step_item(self):
		lead = make_lead(status=self.open_lead, lead_owner=MANAGER)
		frappe.set_user(MANAGER)
		assign({"assign_to": [AGENT], "doctype": "CRM Lead", "name": lead})
		frappe.set_user("Administrator")
		self.idle(lead)
		brief = self.brief()
		self.assertEqual(kind_names(brief, "new"), [lead])
		self.assertEqual(kind_names(brief, "follow_up", "no_next_step"), [])
		self.assertEqual(brief["total"], 1)

	def test_a_waiting_record_is_not_also_a_no_next_step_item(self):
		lead = self.lead(awaiting_reply_since=add_days(now_datetime(), -10))
		self.idle(lead)
		brief = self.brief()
		self.assertEqual(kind_names(brief, "waiting"), [lead])
		self.assertEqual(brief["total"], 1)

	def test_new_means_assigned_to_me_and_not_replied_to(self):
		fresh = make_lead(status=self.open_lead, lead_owner=MANAGER)
		replied = make_lead(status=self.open_lead, lead_owner=MANAGER, last_outbound_at=now_datetime())
		for lead in (fresh, replied):
			frappe.set_user(MANAGER)
			assign({"assign_to": [AGENT], "doctype": "CRM Lead", "name": lead})
			frappe.set_user("Administrator")
		self.assertEqual(kind_names(self.brief(), "new"), [fresh])

	def test_an_item_leaves_once_its_condition_clears(self):
		lead = self.lead(awaiting_reply_since=now_datetime())
		self.assertEqual(kind_names(self.brief(), "waiting"), [lead])
		frappe.db.set_value("CRM Lead", lead, "awaiting_reply_since", None)
		self.assertEqual(kind_names(self.brief(), "waiting"), [])

	def test_count_matches_the_summary_total(self):
		self.lead(awaiting_reply_since=now_datetime())
		self.lead(awaiting_reply_since=add_days(now_datetime(), -31))
		contacted = self.contacted_lead()
		self.follow_up(add_days(nowdate(), -1), reference=contacted)
		self.follow_up(add_days(nowdate(), -31), reference=contacted)
		self.idle_lead()
		brief = get_brief(AGENT)
		self.assertEqual(brief["total"], 3)
		self.assertEqual(get_brief_count(AGENT, "mine"), brief["total"])

	def test_replies_waiting_count_only_from_the_last_30_days(self):
		inside = self.lead(awaiting_reply_since=add_days(now_datetime(), -29))
		self.lead(awaiting_reply_since=add_days(now_datetime(), -31))
		brief = get_brief(AGENT)
		self.assertEqual(kind_names(brief, "waiting"), [inside])
		self.assertEqual(brief["total"], 1)
		self.assertEqual(brief["older"], {"conversations": {"Lead": 1}})

	def test_overdue_follow_ups_count_only_from_the_last_30_days(self):
		contacted = self.contacted_lead()
		inside = self.follow_up(add_days(nowdate(), -29), reference=contacted)
		self.follow_up(add_days(nowdate(), -31), reference=contacted)
		brief = get_brief(AGENT)
		self.assertEqual(kind_names(brief, "follow_up"), [inside])
		self.assertEqual(brief["total"], 1)
		self.assertEqual(brief["older"], {"tasks": 1})

	def test_no_next_step_lists_records_quiet_for_7_to_30_days(self):
		self.idle_lead(days=3)
		quiet = self.idle_lead(days=10)
		self.idle_lead(days=40)
		brief = get_brief(AGENT)
		self.assertEqual(kind_names(brief, "no_next_step"), [quiet])
		self.assertEqual(brief["older"], {})


class TestTeamBrief(TeamWidgetTestCase):
	def brief(self, user=MANAGER):
		return TeamBrief(user).summary()

	def past(self, **kwargs):
		return self.lead(response_by=add_to_date(now_datetime(), hours=-1), **kwargs)

	def test_past_response_clients_come_before_a_longer_wait(self):
		older = self.lead(awaiting_reply_since=add_days(now_datetime(), -9))
		past = self.past()
		self.assertEqual(kind_names(self.brief(), "client"), [past, older])

	def test_a_client_item_says_who_has_it(self):
		self.lead(awaiting_reply_since=now_datetime())
		self.assertEqual(of_kind(self.brief(), "client")[0]["owner"], AGENT)

	def test_a_whatsapp_reply_is_not_past_response(self):
		answered = self.past(last_outbound_at=now_datetime())
		self.assertNotIn(answered, kind_names(self.brief(), "client"))

	def test_a_manager_in_the_hierarchy_gets_no_ownerless_line(self):
		make_lead(status=self.open_lead)
		kinds = [item["kind"] for item in self.brief()["items"]]
		self.assertNotIn("ownerless", kinds)

	def test_a_manager_who_sees_everyone_gets_the_ownerless_line(self):
		make_lead(status=self.open_lead)
		ownerless = of_kind(self.brief(BOSS), "ownerless")
		self.assertEqual(len(ownerless), 1)
		self.assertGreaterEqual(ownerless[0]["count"], 1)

	def test_no_workload_item_when_nobody_is_behind(self):
		self.lead(awaiting_reply_since=now_datetime())
		self.assertEqual(TeamBrief(MANAGER).workload(), [])

	def test_without_an_sla_a_two_day_wait_counts_as_behind(self):
		self.lead(awaiting_reply_since=add_days(now_datetime(), -3))
		workload = TeamBrief(MANAGER).workload()
		self.assertEqual([(row["member"], row["behind"]) for row in workload], [(AGENT, 1)])
		self.assertFalse(workload[0]["past_response"])

	def test_a_record_counts_for_one_person_only(self):
		lead = self.lead(awaiting_reply_since=add_days(now_datetime(), -3))
		assign({"assign_to": [MANAGER], "doctype": "CRM Lead", "name": lead})
		workload = TeamBrief(MANAGER).workload()
		self.assertEqual([row["behind"] for row in workload], [1])

	def test_a_record_with_no_owner_counts_for_its_first_assignee(self):
		lead = self.lead(awaiting_reply_since=add_days(now_datetime(), -3))
		assign({"assign_to": [AGENT], "doctype": "CRM Lead", "name": lead})
		frappe.db.set_value("CRM Lead", lead, "lead_owner", None)
		workload = TeamBrief(MANAGER).workload()
		self.assertEqual([(row["member"], row["behind"]) for row in workload], [(AGENT, 1)])

	def test_someone_with_no_records_is_not_named_as_having_room(self):
		self.lead(awaiting_reply_since=add_days(now_datetime(), -3))
		self.assertIsNone(TeamBrief(MANAGER).workload()[0]["lightest"])

		frappe.set_user("Administrator")
		self.lead(lead_owner=MANAGER)
		self.assertIsNone(TeamBrief(MANAGER).workload()[0]["lightest"])

		self.assertEqual(TeamBrief(BOSS).workload()[0]["lightest"], MANAGER)

	def test_only_someone_who_worked_a_record_in_the_last_30_days_is_named_as_having_room(self):
		self.lead(lead_owner=MANAGER, awaiting_reply_since=add_days(now_datetime(), -3))
		quiet = self.lead()
		frappe.db.set_value(
			"CRM Lead", quiet, "modified", add_days(now_datetime(), -31), update_modified=False
		)
		self.assertIsNone(self.lightest())

		frappe.db.set_value("CRM Lead", quiet, "last_inbound_at", now_datetime(), update_modified=False)
		self.assertEqual(self.lightest(), AGENT)

	def lightest(self):
		return of_kind(get_brief(MANAGER, "team"), "workload")[0]["lightest"]

	def test_the_lightest_person_is_not_the_reader_or_anyone_behind(self):
		self.lead(awaiting_reply_since=add_days(now_datetime(), -3))
		for row in TeamBrief(BOSS).workload():
			self.assertNotIn(row["lightest"], (BOSS, AGENT))

	def test_overdue_follow_ups_are_counted_per_person(self):
		lead = self.lead()
		for _ in range(2):
			make_task(
				add_days(nowdate(), -3),
				assigned_to=AGENT,
				reference_doctype="CRM Lead",
				reference_docname=lead,
			)
		rows = of_kind(self.brief(), "overdue_person")
		self.assertEqual([(row["member"], row["count"]) for row in rows], [(AGENT, 2)])

	def test_count_matches_the_summary_total(self):
		self.past()
		self.lead(awaiting_reply_since=add_days(now_datetime(), -3))
		self.lead(awaiting_reply_since=add_days(now_datetime(), -31))
		self.follow_up(add_days(nowdate(), -31))
		brief = get_brief(MANAGER, "team")
		self.assertEqual(brief["older"], {"conversations": {"Lead": 1}, "tasks": 1})
		self.assertEqual(get_brief_count(MANAGER, "team"), brief["total"])

	def test_replies_waiting_count_only_from_the_last_30_days(self):
		inside = self.lead(awaiting_reply_since=add_days(now_datetime(), -29))
		self.lead(awaiting_reply_since=add_days(now_datetime(), -31))
		brief = get_brief(MANAGER, "team")
		self.assertEqual(kind_names(brief, "client"), [inside])
		self.assertEqual(brief["older"], {"conversations": {"Lead": 1}})

	def test_past_response_counts_only_from_the_last_30_days(self):
		inside = self.lead(response_by=add_days(now_datetime(), -29))
		self.lead(response_by=add_days(now_datetime(), -31))
		brief = get_brief(MANAGER, "team")
		self.assertEqual(kind_names(brief, "client"), [inside])
		self.assertEqual(brief["older"], {"conversations": {"Lead": 1}})

	def test_without_an_sla_behind_counts_only_from_the_last_30_days(self):
		self.lead(awaiting_reply_since=add_days(now_datetime(), -29))
		self.lead(awaiting_reply_since=add_days(now_datetime(), -31))
		workload = of_kind(get_brief(MANAGER, "team"), "workload")
		self.assertEqual([(row["member"], row["behind"]) for row in workload], [(AGENT, 1)])

	def test_with_an_sla_behind_counts_only_from_the_last_30_days(self):
		self.lead(response_by=add_days(now_datetime(), -29))
		self.lead(response_by=add_days(now_datetime(), -31))
		frappe.get_doc(
			{
				"doctype": "CRM Service Level Agreement",
				"name": "Brief window test",
				"sla_name": "Brief window test",
				"apply_on": "CRM Lead",
				"enabled": 1,
			}
		).db_insert()
		workload = of_kind(get_brief(MANAGER, "team"), "workload")
		self.assertEqual([(row["member"], row["behind"]) for row in workload], [(AGENT, 1)])
		self.assertTrue(workload[0]["past_response"])

	def test_overdue_follow_ups_count_only_from_the_last_30_days(self):
		self.follow_up(add_days(nowdate(), -29))
		self.follow_up(add_days(nowdate(), -31))
		brief = get_brief(MANAGER, "team")
		rows = of_kind(brief, "overdue_person")
		self.assertEqual([(row["member"], row["count"]) for row in rows], [(AGENT, 1)])
		self.assertEqual(brief["older"], {"tasks": 1})


class TestBriefDoctype(TeamWidgetTestCase):
	def tearDown(self):
		super().tearDown()
		for user in (AGENT, MANAGER, BOSS):
			clear_defaults_cache(user)

	def set_doctype(self, user, doctype):
		frappe.set_user(user)
		set_brief_doctype(doctype)
		frappe.set_user("Administrator")

	def test_a_new_user_sees_leads_and_deals(self):
		self.assertEqual(get_brief(AGENT)["doctype"], "Both")

	def test_each_user_keeps_their_own_choice(self):
		self.set_doctype(AGENT, "Deal")
		self.set_doctype(MANAGER, "Lead")
		self.assertEqual(get_brief(AGENT)["doctype"], "Deal")
		self.assertEqual(get_brief(MANAGER)["doctype"], "Lead")
		self.assertEqual(get_brief(BOSS)["doctype"], "Both")

	def test_an_agent_can_save_their_own_choice(self):
		self.lead(awaiting_reply_since=now_datetime())
		self.set_doctype(AGENT, "Deal")
		brief = get_brief(AGENT)
		self.assertEqual(brief["items"], [])
		self.assertEqual(get_brief_count(AGENT, "mine"), 0)

	def test_both_clears_the_saved_choice(self):
		self.set_doctype(AGENT, "Deal")
		self.set_doctype(AGENT, "Both")
		self.assertIsNone(frappe.defaults.get_user_default(DOCTYPE_KEY, AGENT))
		self.assertEqual(get_brief(AGENT)["doctype"], "Both")

	def test_only_lead_deal_or_both_can_be_saved(self):
		with self.assertRaises(frappe.ValidationError):
			self.set_doctype(AGENT, "Contact")

	def test_deals_leave_out_the_lead_only_items(self):
		self.lead(lead_owner=MANAGER, awaiting_reply_since=now_datetime())
		make_lead(status=self.open_lead)
		self.set_doctype(MANAGER, "Deal")
		self.set_doctype(BOSS, "Deal")
		self.assertEqual(get_brief(MANAGER)["items"], [])
		self.assertEqual(of_kind(get_brief(BOSS, "team"), "ownerless"), [])

	def test_new_leads_show_with_both_and_not_with_deals(self):
		lead = make_lead(status=self.open_lead, lead_owner=MANAGER)
		frappe.set_user(MANAGER)
		assign({"assign_to": [AGENT], "doctype": "CRM Lead", "name": lead})
		frappe.set_user("Administrator")
		self.assertEqual(kind_names(get_brief(AGENT), "new"), [lead])
		self.set_doctype(AGENT, "Deal")
		self.assertEqual(of_kind(get_brief(AGENT), "new"), [])

	def test_a_widget_with_no_doctype_shows_leads_and_deals(self):
		self.set_doctype(AGENT, "Deal")
		self.lead(awaiting_reply_since=now_datetime())
		self.deal(awaiting_reply_since=now_datetime())
		self.assertEqual(get_tab_data("leads_and_deals", "replies", user=AGENT)["total"], 2)


class TestGetBrief(TeamWidgetTestCase):
	def test_an_agent_gets_their_own_brief(self):
		self.assertEqual(get_brief(AGENT)["tab"], "mine")

	def test_an_agent_cannot_read_the_team_brief_or_its_count(self):
		with self.assertRaises(frappe.PermissionError):
			get_brief(AGENT, "team")
		with self.assertRaises(frappe.PermissionError):
			get_brief_count(AGENT, "team")

	def test_the_brief_leaves_the_other_tab_to_its_own_count(self):
		self.lead(lead_owner=MANAGER, awaiting_reply_since=now_datetime())
		brief = get_brief(MANAGER, "team")
		self.assertEqual(brief["tab"], "team")
		self.assertNotIn("counts", brief)
		self.assertEqual(get_brief_count(MANAGER, "mine"), 1)
		self.assertEqual(get_brief_count(MANAGER, "team"), brief["total"])


class TestBriefTab(TeamWidgetTestCase):
	def tearDown(self):
		super().tearDown()
		for user in (AGENT, MANAGER):
			clear_defaults_cache(user)

	def set_tab(self, user, tab):
		frappe.set_user(user)
		try:
			set_brief_tab(tab)
		finally:
			frappe.set_user("Administrator")

	def test_a_manager_who_has_not_chosen_sees_their_own_brief(self):
		self.assertEqual(get_brief(MANAGER)["tab"], "mine")

	def test_a_manager_comes_back_to_the_tab_they_left(self):
		self.set_tab(MANAGER, "team")
		self.assertEqual(get_brief(MANAGER)["tab"], "team")
		self.set_tab(MANAGER, "mine")
		self.assertIsNone(frappe.defaults.get_user_default(TAB_KEY, MANAGER))
		self.assertEqual(get_brief(MANAGER)["tab"], "mine")

	def test_the_tab_asked_for_wins_over_the_saved_one(self):
		self.set_tab(MANAGER, "team")
		self.assertEqual(get_brief(MANAGER, "mine")["tab"], "mine")

	def test_an_agent_cannot_save_the_team_tab(self):
		with self.assertRaises(frappe.PermissionError):
			self.set_tab(AGENT, "team")

	def test_a_saved_team_tab_falls_back_once_the_user_is_no_manager(self):
		frappe.defaults.set_user_default(TAB_KEY, "team", AGENT)
		self.assertEqual(get_brief(AGENT)["tab"], "mine")

	def test_only_known_tabs_can_be_saved(self):
		with self.assertRaises(frappe.ValidationError):
			self.set_tab(MANAGER, "everyone")


class TestBriefRecords(TeamWidgetTestCase):
	def setUp(self):
		super().setUp()
		month_ago = add_days(now_datetime(), -31)
		self.old_lead = self.lead(awaiting_reply_since=month_ago)
		self.old_deal = self.deal(awaiting_reply_since=month_ago)
		self.old_past_response = self.deal(response_by=month_ago)
		self.recent_lead = self.lead(awaiting_reply_since=add_days(now_datetime(), -29))
		contacted = self.lead(last_outbound_at=now_datetime())
		self.old_task = self.follow_up(add_days(nowdate(), -31), reference=contacted)
		self.recent_task = self.follow_up(add_days(nowdate(), -29), reference=contacted)

	def test_the_names_match_the_older_counts(self):
		for user, tab in ((AGENT, "mine"), (MANAGER, "team")):
			older = get_brief(user, tab)["older"]
			for doctype, count in older["conversations"].items():
				with self.subTest(tab=tab, doctype=doctype):
					self.assertEqual(len(get_brief_records(user, tab, "conversations", doctype)), count)
			with self.subTest(tab=tab, kind="tasks"):
				self.assertEqual(len(get_brief_records(user, tab, "tasks")), older["tasks"])

	def test_both_record_types_have_their_own_count(self):
		older = get_brief(AGENT)["older"]
		self.assertEqual(older["conversations"], {"Lead": 1, "Deal": 1})

	def test_a_past_response_deal_is_an_older_team_conversation(self):
		names = get_brief_records(MANAGER, "team", "conversations", "Deal")
		self.assertIn(self.old_past_response, names)

	def test_records_inside_the_window_are_left_out(self):
		for user, tab in ((AGENT, "mine"), (MANAGER, "team")):
			with self.subTest(tab=tab):
				leads = get_brief_records(user, tab, "conversations", "Lead")
				self.assertIn(self.old_lead, leads)
				self.assertNotIn(self.recent_lead, leads)
				tasks = get_brief_records(user, tab, "tasks")
				self.assertIn(self.old_task, tasks)
				self.assertNotIn(self.recent_task, tasks)

	def test_an_unknown_kind_is_refused(self):
		with self.assertRaises(frappe.ValidationError):
			get_brief_records(AGENT, "mine", "contacts")

	def test_a_record_type_the_brief_does_not_show_is_refused(self):
		frappe.defaults.set_user_default(DOCTYPE_KEY, "Deal", AGENT)
		self.addCleanup(clear_defaults_cache, AGENT)
		with self.assertRaises(frappe.ValidationError):
			get_brief_records(AGENT, "mine", "conversations", "Lead")
		with self.assertRaises(frappe.ValidationError):
			get_brief_records(AGENT, "mine", "conversations", None)

	def test_an_agent_gets_no_team_names(self):
		with self.assertRaises(frappe.PermissionError):
			get_brief_records(AGENT, "team", "conversations", "Lead")


class TestBriefMemberRecords(TeamWidgetTestCase):
	"""Without an SLA, behind means waiting on a reply for more than two days."""

	def setUp(self):
		super().setUp()
		waiting = add_days(now_datetime(), -5)
		self.leads = [self.lead(awaiting_reply_since=waiting)]
		self.deals = [self.deal(awaiting_reply_since=waiting) for _ in range(2)]
		self.someone_elses = self.lead(lead_owner=MANAGER, awaiting_reply_since=waiting)

	def workload_row(self):
		rows = of_kind(get_brief(MANAGER, "team"), "workload")
		return next(row for row in rows if row["member"] == AGENT)

	def test_workload_links_to_the_type_holding_most_records(self):
		row = self.workload_row()
		self.assertEqual(row["behind"], 3)
		self.assertEqual(row["doctype"], "Deal")
		self.assertEqual(row["linked"], 2)

	def test_behind_names_are_the_members_records_of_that_type(self):
		deals = get_brief_records(MANAGER, "team", "behind", "Deal", AGENT)
		leads = get_brief_records(MANAGER, "team", "behind", "Lead", AGENT)
		self.assertCountEqual(deals, self.deals)
		self.assertEqual(leads, self.leads)
		self.assertEqual(len(deals) + len(leads), self.workload_row()["behind"])

	def test_overdue_names_are_the_members_overdue_follow_ups(self):
		mine = self.follow_up(add_days(nowdate(), -3))
		self.follow_up(add_days(nowdate(), -3), assigned_to=MANAGER)
		self.follow_up(add_days(nowdate(), -31))
		row = next(r for r in TeamBrief(MANAGER).overdue_people() if r["member"] == AGENT)
		names = get_brief_records(MANAGER, "team", "overdue", member=AGENT)
		self.assertEqual(names, [mine])
		self.assertEqual(row["count"], 1)

	def test_an_agent_gets_no_team_member_records(self):
		with self.assertRaises(frappe.PermissionError):
			get_brief_records(AGENT, "team", "behind", "Lead", AGENT)
