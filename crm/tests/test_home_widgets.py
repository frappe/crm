import frappe
from frappe.desk.form.assign_to import add as assign
from frappe.desk.form.assign_to import remove as unassign
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, add_to_date, now_datetime, nowdate

from crm.api.home import get_counts, get_tab_data, get_widget_data
from crm.fcrm.doctype.crm_dashboard.home_scope import Mine
from crm.fcrm.doctype.crm_dashboard.home_widgets import (
	DOCTYPES,
	ROW_LIMIT,
	AssignedToMe,
	NoNextStep,
	RepliesWaiting,
)
from crm.tests.test_home import (
	AGENT,
	MANAGER,
	make_deal,
	make_lead,
	make_task,
	make_user,
	without_forecasting,
)


def status(doctype, *types):
	return frappe.get_all(doctype, filters={"type": ["in", types]}, pluck="name")[0]


def names(data):
	return [row["name"] for row in data["rows"]]


class HomeWidgetTestCase(IntegrationTestCase):
	def setUp(self):
		without_forecasting()
		make_user(AGENT, "Sales User")
		make_user(MANAGER, "Sales User", "Sales Manager")
		self.open_lead = status("CRM Lead Status", "Open")
		self.ongoing_lead = status("CRM Lead Status", "Ongoing")
		self.closed_lead = status("CRM Lead Status", "Won")
		self.open_deal = status("CRM Deal Status", "Open", "Ongoing")
		self.closed_deal = status("CRM Deal Status", "Won")
		self.new_deal = status("CRM Deal Status", "Open")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def data(self, widget, doctype="Both"):
		return widget(DOCTYPES[doctype], Mine(AGENT)).summary()

	def counts(self):
		frappe.set_user(AGENT)
		counts = get_counts()
		frappe.set_user("Administrator")
		return counts

	def lead(self, **kwargs):
		return make_lead(**{"lead_owner": AGENT, "status": self.open_lead, **kwargs})

	def deal(self, **kwargs):
		return make_deal(**{"deal_owner": AGENT, "status": self.open_deal, **kwargs})

	def follow_up(self, due_date, doctype="CRM Lead", reference=None, **kwargs):
		reference = reference or self.lead()
		return make_task(
			due_date,
			reference_doctype=doctype,
			reference_docname=reference,
			**{"assigned_to": AGENT, **kwargs},
		).name


class TestRepliesWaiting(HomeWidgetTestCase):
	def test_shows_my_open_records_oldest_wait_first(self):
		newer = self.lead(awaiting_reply_since=add_to_date(now_datetime(), hours=-1))
		older = self.deal(awaiting_reply_since=add_to_date(now_datetime(), hours=-5))
		self.lead()
		self.lead(lead_owner=MANAGER, awaiting_reply_since=now_datetime())
		self.lead(awaiting_reply_since=now_datetime(), converted=1)
		self.lead(awaiting_reply_since=now_datetime(), status=self.closed_lead)
		self.deal(awaiting_reply_since=now_datetime(), status=self.closed_deal)

		data = self.data(RepliesWaiting)
		self.assertEqual(names(data), [older, newer])
		self.assertEqual(data["total"], 2)
		self.assertEqual(self.counts()["replies_waiting"], 2)

	def test_doctype_setting_picks_leads_or_deals(self):
		lead = self.lead(awaiting_reply_since=now_datetime())
		deal = self.deal(awaiting_reply_since=now_datetime())
		self.assertEqual(names(self.data(RepliesWaiting, "Lead")), [lead])
		self.assertEqual(names(self.data(RepliesWaiting, "Deal")), [deal])

	def test_assigned_records_are_mine(self):
		lead = self.lead(lead_owner=MANAGER, awaiting_reply_since=now_datetime())
		assign({"assign_to": [AGENT], "doctype": "CRM Lead", "name": lead})
		self.assertEqual(names(self.data(RepliesWaiting)), [lead])

	def test_rows_are_capped_but_total_counts_all(self):
		for _ in range(ROW_LIMIT + 2):
			self.lead(awaiting_reply_since=now_datetime())
		data = self.data(RepliesWaiting)
		self.assertEqual(len(data["rows"]), ROW_LIMIT)
		self.assertEqual(data["total"], ROW_LIMIT + 2)


class TestReplyChannel(HomeWidgetTestCase):
	def setUp(self):
		super().setUp()
		if not frappe.db.table_exists("WA Message"):
			self.skipTest("WhatsApp is not installed")

	def channel(self):
		return {row["name"]: row["channel"] for row in self.data(RepliesWaiting)["rows"]}

	def test_channel_is_the_latest_inbound_message(self):
		emailed = self.lead(awaiting_reply_since=now_datetime())
		messaged = self.lead(awaiting_reply_since=now_datetime())
		unknown = self.lead(awaiting_reply_since=now_datetime())
		received_email("CRM Lead", emailed, add_to_date(now_datetime(), hours=-1))
		received_email("CRM Lead", messaged, add_to_date(now_datetime(), hours=-3))
		received_whatsapp("CRM Lead", messaged, add_to_date(now_datetime(), hours=-1))
		received_whatsapp("CRM Lead", emailed, add_to_date(now_datetime(), hours=-2))

		self.assertEqual(self.channel(), {emailed: "email", messaged: "whatsapp", unknown: None})

	def test_deal_uses_messages_on_its_converted_lead(self):
		lead = self.lead(converted=1)
		deal = self.deal(lead=lead, awaiting_reply_since=now_datetime())
		received_whatsapp("CRM Lead", lead, now_datetime())
		self.assertEqual(self.channel(), {deal: "whatsapp"})


class TestAssignedToMe(HomeWidgetTestCase):
	def test_newest_assignment_first(self):
		first = self.lead(lead_owner=None)
		second = self.deal(deal_owner=None, status=self.open_deal)
		assign({"assign_to": [AGENT], "doctype": "CRM Lead", "name": first})
		frappe.db.set_value("ToDo", {"reference_name": first}, "creation", add_days(now_datetime(), -1))
		assign({"assign_to": [AGENT], "doctype": "CRM Deal", "name": second})

		data = self.data(AssignedToMe)
		self.assertEqual(names(data), [second, first])
		self.assertEqual(data["total"], 2)

	def test_only_open_assignments_on_active_records(self):
		owned_only = self.lead(lead_owner=None)
		frappe.db.set_value("CRM Lead", owned_only, "lead_owner", AGENT, update_modified=False)
		removed = self.lead(lead_owner=None)
		assign({"assign_to": [AGENT], "doctype": "CRM Lead", "name": removed})
		unassign("CRM Lead", removed, AGENT)
		self.lead(status=self.closed_lead)
		ongoing = self.lead(status=self.ongoing_lead)

		self.assertEqual(names(self.data(AssignedToMe)), [ongoing])


class TestNoNextStep(HomeWidgetTestCase):
	def idle(self, name, days, doctype="CRM Lead", **values):
		frappe.db.set_value(
			doctype, name, {"modified": add_days(now_datetime(), -days), **values}, update_modified=False
		)
		return name

	def test_idle_records_without_an_open_follow_up_longest_idle_first(self):
		idle = self.idle(self.lead(), 9)
		idler = self.idle(self.deal(), 20, "CRM Deal")
		self.idle(self.lead(), 3)
		self.idle(self.lead(), 9, last_inbound_at=add_days(now_datetime(), -1))
		self.idle(self.lead(status=self.closed_lead), 30)

		data = self.data(NoNextStep)
		self.assertEqual(names(data), [idler, idle])
		self.assertEqual(data["total"], 2)

	def test_an_open_follow_up_is_a_next_step(self):
		planned = self.lead()
		make_task(add_days(nowdate(), 3), reference_doctype="CRM Lead", reference_docname=planned)
		done = self.lead()
		make_task(nowdate(), reference_doctype="CRM Lead", reference_docname=done, status="Done")
		self.idle(planned, 10)
		self.idle(done, 10)

		self.assertEqual(names(self.data(NoNextStep)), [done])


class TestTasksWidget(HomeWidgetTestCase):
	def tasks(self, tab="all"):
		return get_tab_data("tasks", tab, user=AGENT)

	def test_all_lists_my_open_tasks_by_due_date_undated_last(self):
		undated = make_task(None, assigned_to=AGENT).name
		later = make_task(add_days(nowdate(), 20), assigned_to=AGENT).name
		overdue = self.follow_up(add_days(now_datetime(), -2))
		upcoming = self.follow_up(add_days(nowdate(), 3), all_day=1)
		self.follow_up(add_days(now_datetime(), -1), status="Done")
		self.follow_up(add_days(now_datetime(), -1), assigned_to=MANAGER)

		data = self.tasks()
		self.assertEqual(names(data), [overdue, upcoming, later, undated])
		self.assertEqual(data["total"], 4)
		self.assertEqual(data["counts"], {"all": 4, "due": 1, "upcoming": 1, "unlinked": 2})

	def test_due_puts_overdue_first_and_includes_unlinked_tasks(self):
		today = self.follow_up(nowdate(), all_day=1)
		overdue = self.follow_up(add_days(now_datetime(), -2))
		unlinked = make_task(add_days(now_datetime(), -1), assigned_to=AGENT).name
		self.follow_up(add_days(now_datetime(), 3))

		data = self.tasks("due")
		self.assertEqual(names(data), [overdue, unlinked, today])
		self.assertEqual(data["rows"][0]["reference_title"], "Home")
		self.assertEqual(self.counts()["follow_ups_due"], 2)

	def test_upcoming_covers_the_next_seven_days(self):
		later = self.follow_up(add_days(nowdate(), 7), all_day=1)
		tomorrow = self.follow_up(add_days(nowdate(), 1), all_day=1)
		self.follow_up(nowdate(), all_day=1)
		self.follow_up(add_days(nowdate(), 8), all_day=1)

		self.assertEqual(names(self.tasks("upcoming")), [tomorrow, later])

	def test_unlinked_are_open_tasks_without_a_record(self):
		undated = make_task(None, assigned_to=AGENT).name
		dated = make_task(add_days(nowdate(), 2), assigned_to=AGENT).name
		make_task(nowdate(), assigned_to=AGENT, status="Done")
		make_task(nowdate(), assigned_to=MANAGER)
		self.follow_up(nowdate())

		self.assertEqual(names(self.tasks("unlinked")), [dated, undated])

	def test_unknown_tab_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self.tasks("done")


class TestLeadsAndDealsWidget(HomeWidgetTestCase):
	def test_new_lists_my_open_records_newest_first_with_tab_counts(self):
		older = self.lead()
		frappe.db.set_value("CRM Lead", older, "creation", add_days(now_datetime(), -2))
		newer = self.deal(status=self.new_deal)
		self.lead(status=self.ongoing_lead)
		self.lead(lead_owner=MANAGER)
		waiting = self.lead(status=self.ongoing_lead, awaiting_reply_since=now_datetime())

		data = get_tab_data("leads_and_deals", "new", user=AGENT)
		self.assertEqual(names(data), [newer, older])
		self.assertEqual(data["counts"], {"replies": 1, "new": 2})
		self.assertEqual(names(get_tab_data("leads_and_deals", "replies", user=AGENT)), [waiting])

	def test_doctype_setting_applies_to_every_tab(self):
		lead = self.lead()
		self.deal(status=self.new_deal)
		data = get_tab_data("leads_and_deals", "new", "Lead", AGENT)
		self.assertEqual(names(data), [lead])
		self.assertEqual(data["counts"]["new"], 1)


class TestRecentActivity(HomeWidgetTestCase):
	def act(self, doctype, values, days_ago=0, user=AGENT):
		frappe.set_user(user)
		doc = frappe.get_doc({"doctype": doctype, **values}).insert(ignore_permissions=True)
		frappe.set_user("Administrator")
		frappe.db.set_value(doctype, doc.name, "creation", add_days(now_datetime(), -days_ago))
		return doc

	def view(self, lead, days_ago=0, user=AGENT):
		values = {"viewed_by": user, "reference_doctype": "CRM Lead", "reference_name": lead}
		return self.act("View Log", values, days_ago, user)

	def comment(self, lead, days_ago=0):
		values = {
			"comment_type": "Comment",
			"reference_doctype": "CRM Lead",
			"reference_name": lead,
			"content": "Called back",
		}
		return self.act("Comment", values, days_ago)

	def activity(self):
		rows = get_widget_data("recently_opened", user=AGENT)["rows"]
		return [(row["name"], row["activity"]) for row in rows]

	def test_latest_action_per_record_newest_first(self):
		viewed, commented = self.lead(), self.lead()
		self.view(viewed, days_ago=1)
		self.view(commented, days_ago=3)
		self.comment(commented, days_ago=2)

		self.assertEqual(self.activity(), [(viewed, "Viewed"), (commented, "Commented")])

	def test_names_a_status_change(self):
		lead = frappe.get_doc("CRM Lead", self.lead())
		frappe.set_user(AGENT)
		lead.status = self.ongoing_lead
		lead.save(ignore_permissions=True, ignore_version=False)
		frappe.set_user("Administrator")

		self.assertEqual(self.activity(), [(lead.name, f"Set status to {self.ongoing_lead}")])

	def test_leaves_out_others_and_old_activity(self):
		lead = self.lead()
		self.view(lead, user=MANAGER)
		self.view(lead, days_ago=10)
		self.assertEqual(self.activity(), [])


class TestWidgetValidation(HomeWidgetTestCase):
	def test_unknown_widget_or_doctype_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			get_widget_data("sales_trend")
		with self.assertRaises(frappe.ValidationError):
			get_widget_data("no_next_step", "Contact")
		with self.assertRaises(frappe.ValidationError):
			get_tab_data("no_next_step", "all")
		with self.assertRaises(frappe.ValidationError):
			get_tab_data("leads_and_deals", "new", "Contact")


def received_email(doctype, name, at):
	frappe.get_doc(
		{
			"doctype": "Communication",
			"name": frappe.generate_hash(),
			"communication_type": "Communication",
			"communication_medium": "Email",
			"sent_or_received": "Received",
			"subject": "Re: pricing",
			"reference_doctype": doctype,
			"reference_name": name,
			"communication_date": at,
		}
	).db_insert()


def received_whatsapp(doctype, name, at):
	frappe.get_doc(
		{
			"doctype": "WA Message",
			"name": frappe.generate_hash(),
			"direction": "Incoming",
			"docstatus": 1,
			"reference_doctype": doctype,
			"reference_docname": name,
			"timestamp": at,
		}
	).db_insert()
