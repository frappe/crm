from contextlib import contextmanager
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import frappe
from frappe.desk.form.assign_to import add as assign
from frappe.utils import add_days, add_to_date, get_system_timezone, now_datetime

from crm.api.digest import LAST_RUN_KEY, OPT_OUT_KEY, MorningDigest, send_morning_digests
from crm.api.home import set_morning_digest
from crm.tests.test_home import AGENT, MANAGER, make_task
from crm.tests.test_home_widgets import HomeWidgetTestCase

ZONES = {AGENT: "Asia/Kolkata", MANAGER: "America/New_York"}


def system_time(user_zone: str, *wall_time):
	"""The naive system time at which a clock in `user_zone` shows `wall_time`."""
	local = datetime(*wall_time, tzinfo=ZoneInfo(user_zone))
	return local.astimezone(ZoneInfo(get_system_timezone())).replace(tzinfo=None)


def queued(user=AGENT):
	return frappe.get_all(
		"Email Queue",
		filters={"name": ["in", recipients_queue(user)], "message": ["like", "%Your CRM morning%"]},
		fields=["name", "message"],
	)


def recipients_queue(user):
	return frappe.get_all("Email Queue Recipient", filters={"recipient": user}, pluck="parent") or [""]


@contextmanager
def user_zones():
	with patch(
		"crm.fcrm.doctype.crm_task.rules._user_time_zone", side_effect=lambda user: ZONES.get(user, "UTC")
	):
		yield


class DigestTestCase(HomeWidgetTestCase):
	def setUp(self):
		super().setUp()
		frappe.defaults.clear_user_default(LAST_RUN_KEY, AGENT)
		frappe.defaults.clear_user_default(OPT_OUT_KEY, AGENT)
		zones = user_zones()
		zones.__enter__()
		self.addCleanup(zones.__exit__, None, None, None)

	def sections(self):
		return {section.title: section for section in MorningDigest(AGENT).sections()}

	def today(self, days=0):
		"""The agent's local date, as all-day tasks store it."""
		return add_days(MorningDigest(AGENT).due.today, days)


class TestDigestTiming(DigestTestCase):
	def test_due_between_eight_and_eleven_local_time(self):
		self.assertFalse(MorningDigest(AGENT, system_time("Asia/Kolkata", 2026, 10, 24, 7, 59)).is_due())
		self.assertTrue(MorningDigest(AGENT, system_time("Asia/Kolkata", 2026, 10, 24, 8, 30)).is_due())
		self.assertFalse(MorningDigest(AGENT, system_time("Asia/Kolkata", 2026, 10, 24, 11, 0)).is_due())

	def test_same_instant_is_morning_for_one_zone_only(self):
		now = system_time("Asia/Kolkata", 2026, 10, 24, 8, 30)
		self.assertTrue(MorningDigest(AGENT, now).is_due())
		self.assertFalse(MorningDigest(MANAGER, now).is_due())

	def test_runs_once_a_local_day(self):
		now = system_time("Asia/Kolkata", 2026, 10, 24, 8, 0)
		MorningDigest(AGENT, now).send()
		self.assertFalse(MorningDigest(AGENT, add_to_date(now, hours=1)).is_due())
		self.assertTrue(MorningDigest(AGENT, add_days(now, 1)).is_due())

	def test_opted_out_user_is_never_due(self):
		morning = system_time("Asia/Kolkata", 2026, 10, 24, 8, 30)
		frappe.set_user(AGENT)
		set_morning_digest(False)
		self.assertFalse(MorningDigest(AGENT, morning).is_due())
		set_morning_digest(True)
		self.assertTrue(MorningDigest(AGENT, morning).is_due())
		frappe.set_user("Administrator")


class TestDigestSending(DigestTestCase):
	def setUp(self):
		super().setUp()
		frappe.db.set_single_value("FCRM Settings", "enable_morning_digest", 1)
		if not frappe.db.exists("Email Account", {"default_outgoing": 1}):
			make_outgoing_email_account()

	def run_job(self, users=(AGENT,)):
		with (
			patch("crm.api.digest.sales_users", return_value=list(users)),
			patch(
				"crm.api.digest.now_datetime", return_value=system_time("Asia/Kolkata", 2026, 10, 24, 9, 0)
			),
		):
			send_morning_digests()

	def test_sends_the_digest_once(self):
		self.lead(awaiting_reply_since=now_datetime())
		self.follow_up(now_datetime())

		self.run_job()
		self.run_job()

		emails = queued()
		self.assertEqual(len(emails), 1)
		self.assertIn("Replies waiting", emails[0].message)
		self.assertIn("/crm", emails[0].message)

	def test_one_failing_user_does_not_stop_the_others(self):
		self.lead(awaiting_reply_since=now_datetime())
		with (
			patch.dict(ZONES, {MANAGER: "Not/AZone"}),
			patch("crm.api.digest.frappe.log_error") as log_error,
		):
			self.run_job(users=(MANAGER, AGENT))
		log_error.assert_called_once()
		self.assertEqual(len(queued()), 1)

	def test_skips_when_every_section_is_empty(self):
		self.run_job()
		self.assertEqual(queued(), [])
		self.assertIsNotNone(frappe.defaults.get_user_default(LAST_RUN_KEY, AGENT))

	def test_site_toggle_and_user_opt_out_stop_it(self):
		self.lead(awaiting_reply_since=now_datetime())

		frappe.db.set_single_value("FCRM Settings", "enable_morning_digest", 0)
		self.run_job()
		self.assertEqual(queued(), [])

		frappe.db.set_single_value("FCRM Settings", "enable_morning_digest", 1)
		frappe.defaults.set_user_default(OPT_OUT_KEY, "0", AGENT)
		self.run_job()
		self.assertEqual(queued(), [])

	def test_subject_counts_follow_ups_and_replies(self):
		self.lead(awaiting_reply_since=now_datetime())
		self.follow_up(now_datetime())
		self.follow_up(now_datetime())
		digest = MorningDigest(AGENT)
		self.assertEqual(digest.subject(digest.sections()), "Your CRM morning: 2 follow-ups, 1 reply waiting")


class TestDigestSections(DigestTestCase):
	def titles(self, section):
		return [item["title"] for item in section["items"]]

	def test_follow_ups_overdue_in_the_last_thirty_days_and_due_today(self):
		self.follow_up(add_days(now_datetime(), -3), title="Recent miss")
		self.follow_up(self.today(), all_day=1, title="Today")
		self.follow_up(add_days(now_datetime(), -40), title="Abandoned")
		self.follow_up(self.today(1), all_day=1, title="Tomorrow")
		make_task(self.today(), all_day=1, assigned_to=AGENT, title="Standalone")

		sections = self.sections()
		self.assertEqual(self.titles(sections["Follow-ups due"]), ["Recent miss", "Today"])
		self.assertEqual(self.titles(sections["Tasks due today"]), ["Standalone"])

	def test_tasks_due_today_leave_out_other_days(self):
		make_task(self.today(), all_day=1, assigned_to=AGENT, title="Today")
		make_task(self.today(-1), all_day=1, assigned_to=AGENT, title="Yesterday")
		make_task(self.today(1), all_day=1, assigned_to=AGENT, title="Tomorrow")
		self.assertEqual(self.titles(self.sections()["Tasks due today"]), ["Today"])

	def test_replies_waiting(self):
		lead = self.lead(awaiting_reply_since=now_datetime(), first_name="Priya")
		section = self.sections()["Replies waiting"]
		self.assertEqual(section.total, 1)
		self.assertIn(f"/crm/leads/{lead}", section["items"][0]["url"])

	def test_newly_assigned_since_the_last_digest(self):
		before = self.lead(lead_owner=None, first_name="Before")
		after = self.lead(lead_owner=None, first_name="After")
		assign({"assign_to": [AGENT], "doctype": "CRM Lead", "name": before})
		frappe.db.set_value("ToDo", {"reference_name": before}, "creation", add_days(now_datetime(), -2))
		frappe.defaults.set_user_default(LAST_RUN_KEY, str(add_days(now_datetime(), -1)), AGENT)
		assign({"assign_to": [AGENT], "doctype": "CRM Lead", "name": after})
		mine = self.lead(lead_owner=None, first_name="Mine")
		assign({"assign_to": [AGENT], "doctype": "CRM Lead", "name": mine})
		frappe.db.set_value("ToDo", {"reference_name": mine}, "assigned_by", AGENT)

		self.assertEqual(self.titles(self.sections()["Newly assigned to you"]), ["After"])


def make_outgoing_email_account():
	frappe.get_doc(
		{
			"doctype": "Email Account",
			"email_account_name": "_Test Digest Outgoing",
			"email_id": "digest.outgoing@example.com",
			"enable_outgoing": 1,
			"default_outgoing": 1,
			"smtp_server": "localhost",
			"no_smtp_authentication": 1,
		}
	).insert(ignore_permissions=True)
