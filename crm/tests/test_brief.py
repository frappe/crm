import frappe
from frappe.desk.form.assign_to import add as assign
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, add_to_date, now_datetime, nowdate

from crm.fcrm.doctype.crm_dashboard.brief import MineBrief, TeamBrief, allocate, get_brief
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

	def idle(self, lead):
		frappe.db.set_value(
			"CRM Lead", lead, {"modified": add_days(now_datetime(), -10)}, update_modified=False
		)

	def idle_lead(self):
		lead = self.lead()
		self.idle(lead)
		frappe.db.set_value("ToDo", {"reference_name": lead}, "creation", add_days(now_datetime(), -10))
		return lead

	def test_a_quiet_day_has_no_groups(self):
		brief = self.brief()
		self.assertEqual(brief, {"items": [], "total": 0})

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
		make_task(
			add_days(nowdate(), -1),
			assigned_to=AGENT,
			reference_doctype="CRM Lead",
			reference_docname=self.lead(),
		)
		self.assertEqual(MineBrief(AGENT).count(), self.brief()["total"])


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

	def test_someone_with_no_records_is_not_named_as_having_room(self):
		self.lead(awaiting_reply_since=add_days(now_datetime(), -3))
		self.assertIsNone(TeamBrief(MANAGER).workload()[0]["lightest"])

		frappe.set_user("Administrator")
		self.lead(lead_owner=MANAGER)
		self.assertIsNone(TeamBrief(MANAGER).workload()[0]["lightest"])

		self.assertEqual(TeamBrief(BOSS).workload()[0]["lightest"], MANAGER)

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
		self.assertEqual(TeamBrief(MANAGER).count(), self.brief()["total"])


class TestGetBrief(TeamWidgetTestCase):
	def test_an_agent_gets_their_own_brief_with_no_tabs(self):
		brief = get_brief(AGENT)
		self.assertNotIn("counts", brief)

	def test_an_agent_cannot_read_the_team_brief(self):
		with self.assertRaises(frappe.PermissionError):
			get_brief(AGENT, "team")

	def test_a_manager_gets_counts_for_both_tabs(self):
		self.lead(lead_owner=MANAGER, awaiting_reply_since=now_datetime())
		brief = get_brief(MANAGER, "team")
		self.assertEqual(brief["tab"], "team")
		self.assertEqual(set(brief["counts"]), {"team", "mine"})
		self.assertEqual(brief["counts"]["mine"], 1)
