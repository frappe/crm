import frappe
from frappe.desk.form.assign_to import add as assign
from frappe.desk.form.assign_to import remove as unassign
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, add_to_date, now_datetime, nowdate

from crm.api.home import get_counts, get_widget_data
from crm.fcrm.doctype.crm_dashboard.home_widgets import ROW_LIMIT
from crm.tests.test_home import (
	AGENT,
	MANAGER,
	make_deal,
	make_lead,
	make_task,
	make_user,
	reply_columns,
	unreadable,
)


def status(doctype, *types):
	return frappe.get_all(doctype, filters={"type": ["in", types]}, pluck="name")[0]


def names(data):
	return [row["name"] for row in data["rows"]]


class HomeWidgetTestCase(IntegrationTestCase):
	def setUp(self):
		make_user(AGENT, "Sales User")
		make_user(MANAGER, "Sales User", "Sales Manager")
		self.open_lead = status("CRM Lead Status", "Open")
		self.ongoing_lead = status("CRM Lead Status", "Ongoing")
		self.closed_lead = status("CRM Lead Status", "Won")
		self.open_deal = status("CRM Deal Status", "Open", "Ongoing")
		self.closed_deal = status("CRM Deal Status", "Won")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def data(self, widget, doctype="Both", columns=None):
		return get_widget_data(widget, doctype, AGENT, columns)

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

		data = self.data("replies_waiting")
		self.assertEqual(names(data), [older, newer])
		self.assertEqual(data["total"], 2)
		self.assertEqual(self.counts()["replies_waiting"], 2)

	def test_doctype_setting_picks_leads_or_deals(self):
		lead = self.lead(awaiting_reply_since=now_datetime())
		deal = self.deal(awaiting_reply_since=now_datetime())
		self.assertEqual(names(self.data("replies_waiting", "Lead")), [lead])
		self.assertEqual(names(self.data("replies_waiting", "Deal")), [deal])

	def test_assigned_records_are_mine(self):
		lead = self.lead(lead_owner=MANAGER, awaiting_reply_since=now_datetime())
		assign({"assign_to": [AGENT], "doctype": "CRM Lead", "name": lead})
		self.assertEqual(names(self.data("replies_waiting")), [lead])

	def test_rows_are_capped_but_total_counts_all(self):
		for _ in range(ROW_LIMIT + 2):
			self.lead(awaiting_reply_since=now_datetime())
		data = self.data("replies_waiting")
		self.assertEqual(len(data["rows"]), ROW_LIMIT)
		self.assertEqual(data["total"], ROW_LIMIT + 2)


class TestReplyChannel(HomeWidgetTestCase):
	def setUp(self):
		super().setUp()
		if not frappe.db.table_exists("WA Message"):
			self.skipTest("WhatsApp is not installed")

	def channel(self):
		return {row["name"]: row["channel"] for row in self.data("replies_waiting")["rows"]}

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

		data = self.data("assigned_to_me")
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

		self.assertEqual(names(self.data("assigned_to_me")), [ongoing])


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

		data = self.data("no_next_step")
		self.assertEqual(names(data), [idler, idle])
		self.assertEqual(data["total"], 2)

	def test_an_open_follow_up_is_a_next_step(self):
		planned = self.lead()
		make_task(add_days(nowdate(), 3), reference_doctype="CRM Lead", reference_docname=planned)
		done = self.lead()
		make_task(nowdate(), reference_doctype="CRM Lead", reference_docname=done, status="Done")
		self.idle(planned, 10)
		self.idle(done, 10)

		self.assertEqual(names(self.data("no_next_step")), [done])


class TestFollowUpWidgets(HomeWidgetTestCase):
	def test_follow_ups_due_puts_overdue_first_and_matches_the_header(self):
		today = self.follow_up(nowdate(), all_day=1)
		overdue = self.follow_up(add_days(now_datetime(), -2))
		self.follow_up(add_days(now_datetime(), 3))
		self.follow_up(add_days(now_datetime(), -1), status="Done")
		self.follow_up(add_days(now_datetime(), -1), assigned_to=MANAGER)
		make_task(add_days(now_datetime(), -1), assigned_to=AGENT)

		data = self.data("follow_ups_due")
		self.assertEqual(names(data), [overdue, today])
		self.assertEqual(data["total"], self.counts()["follow_ups_due"])
		self.assertEqual(data["rows"][0]["reference_title"], "Home")

	def test_follow_ups_follow_the_doctype_setting(self):
		on_lead = self.follow_up(nowdate(), all_day=1)
		on_deal = self.follow_up(nowdate(), "CRM Deal", self.deal(), all_day=1)
		self.assertEqual(names(self.data("follow_ups_due", "Lead")), [on_lead])
		self.assertEqual(names(self.data("follow_ups_due", "Deal")), [on_deal])

	def test_upcoming_covers_the_next_seven_days(self):
		later = self.follow_up(add_days(nowdate(), 7), all_day=1)
		tomorrow = self.follow_up(add_days(nowdate(), 1), all_day=1)
		self.follow_up(nowdate(), all_day=1)
		self.follow_up(add_days(nowdate(), 8), all_day=1)

		self.assertEqual(names(self.data("upcoming_follow_ups")), [tomorrow, later])

	def test_my_tasks_are_open_standalone_tasks(self):
		undated = make_task(None, assigned_to=AGENT).name
		dated = make_task(add_days(nowdate(), 2), assigned_to=AGENT).name
		make_task(nowdate(), assigned_to=AGENT, status="Done")
		make_task(nowdate(), assigned_to=MANAGER)
		self.follow_up(nowdate())

		data = self.data("my_tasks")
		self.assertEqual(names(data), [dated, undated])
		self.assertEqual(data["total"], 2)


class TestWidgetColumns(HomeWidgetTestCase):
	def test_rows_carry_the_requested_fields(self):
		self.lead(awaiting_reply_since=now_datetime(), territory=None)
		self.deal(awaiting_reply_since=now_datetime())
		rows = self.data("replies_waiting", columns=reply_columns("owner", "territory"))["rows"]
		self.assertEqual([row["owner"] for row in rows], [AGENT, AGENT])
		self.assertTrue(all("territory" in row for row in rows))

	def test_currency_columns_carry_the_row_currency(self):
		self.deal(awaiting_reply_since=now_datetime(), deal_value=500, currency="EUR")
		row = self.data("replies_waiting", "Deal", reply_columns("deal_value"))["rows"][0]
		self.assertEqual((row["deal_value"], row["currency"]), (500, "EUR"))

	def test_task_rows_carry_the_requested_fields(self):
		make_task(nowdate(), assigned_to=AGENT, start_date=nowdate())
		columns = [{"key": key} for key in ("title", "due_date", "start_date")]
		row = self.data("my_tasks", columns=columns)["rows"][0]
		self.assertEqual(str(row["start_date"]), nowdate())

	def test_disallowed_and_unreadable_fields_are_not_fetched(self):
		self.lead(awaiting_reply_since=now_datetime(), lead_score=7)
		row = self.data("replies_waiting", "Lead", reply_columns("lead_score"))["rows"][0]
		self.assertEqual(row["lead_score"], 7)

		with unreadable("CRM Lead", "lead_score"):
			row = self.data("replies_waiting", "Lead", reply_columns("lead_score"))["rows"][0]
		self.assertNotIn("lead_score", row)
		for key in ("deal_value", "not_a_field", "image"):
			row = self.data("replies_waiting", "Lead", reply_columns(key))["rows"][0]
			self.assertNotIn(key, row)

	def test_default_columns_fetch_no_extra_fields(self):
		self.lead(awaiting_reply_since=now_datetime())
		row = self.data("replies_waiting")["rows"][0]
		self.assertEqual(
			set(row), {"name", "status", "title", "subtitle", "awaiting_reply_since", "doctype", "channel"}
		)


class TestWidgetValidation(HomeWidgetTestCase):
	def test_unknown_widget_or_doctype_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			get_widget_data("recently_opened")
		with self.assertRaises(frappe.ValidationError):
			get_widget_data("replies_waiting", "Contact")


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
