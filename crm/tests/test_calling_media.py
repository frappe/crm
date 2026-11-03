# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from crm.integrations.api import get_calling_media, link_to_call_log
from crm.tests.test_password_setup import make_user


class TestCallingMedia(IntegrationTestCase):
	def setUp(self):
		self.user = make_user("calling-media-46116@example.com", roles=["Sales User"]).name
		frappe.set_user(self.user)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def make_agent(self, **values):
		frappe.get_doc(doctype="CRM Telephony Agent", user=self.user, **values).insert(
			ignore_permissions=True
		)

	def enable(self, twilio=0, exotel=0):
		frappe.db.set_single_value("CRM Twilio Settings", "enabled", twilio)
		frappe.db.set_single_value("CRM Exotel Settings", "enabled", exotel)

	def test_a_user_without_an_agent_row_has_no_medium(self):
		self.enable(twilio=1, exotel=1)
		self.assertEqual(get_calling_media(), {"media": [], "default_medium": None, "live_exotel_call": None})

	def test_a_medium_needs_its_site_flag_and_the_agents_number(self):
		self.make_agent(twilio_number="+15550100001", exotel_number="+918880000001")
		self.enable(twilio=1, exotel=0)
		self.assertEqual(get_calling_media()["media"], ["Twilio"])

		self.enable(twilio=1, exotel=1)
		self.assertEqual(get_calling_media()["media"], ["Twilio", "Exotel"])

	def test_an_enabled_site_without_the_agents_number_is_not_a_medium(self):
		self.make_agent(exotel_number="+918880000001")
		self.enable(twilio=1, exotel=1)
		self.assertEqual(get_calling_media()["media"], ["Exotel"])

	def test_the_default_is_kept_only_while_its_medium_is_usable(self):
		self.make_agent(twilio_number="+15550100001", default_medium="Exotel")
		self.enable(twilio=1, exotel=1)
		self.assertIsNone(get_calling_media()["default_medium"])

	def make_exotel_log(self, sid, **values):
		fields = {
			"type": "Incoming",
			"status": "Ringing",
			"telephony_medium": "Exotel",
			"medium": "+918880000001",
			"from": "+915550100100",
			"to": "+919999900001",
		}
		frappe.get_doc(doctype="CRM Call Log", id=sid, **(fields | values)).insert(ignore_permissions=True)

	def test_a_live_exotel_call_of_the_user_comes_with_the_media(self):
		self.make_agent(exotel_number="+918880000001")
		self.enable(exotel=1)
		self.make_exotel_log("t46118-live", receiver=self.user, **{"from": "+915550100101"})
		self.make_exotel_log("t46118-other", receiver="Administrator", **{"from": "+915550100102"})
		self.make_exotel_log("t46118-over", receiver=self.user, status="Completed")

		live = get_calling_media()["live_exotel_call"]
		self.assertEqual(live["call_sid"], "t46118-live")
		self.assertEqual(
			(live["incoming"], live["number"], live["status"]), (True, "+915550100101", "Ringing")
		)

	def test_an_outgoing_live_call_shows_the_customer_and_an_old_one_is_dropped(self):
		self.make_agent(exotel_number="+918880000001")
		self.enable(exotel=1)
		self.make_exotel_log(
			"t46118-out", type="Outgoing", status="In Progress", caller=self.user, to="+915550100103"
		)
		live = get_calling_media()["live_exotel_call"]
		self.assertEqual(
			(live["incoming"], live["number"], live["status"]), (False, "+915550100103", "In Progress")
		)

		frappe.db.set_value(
			"CRM Call Log", "t46118-out", "creation", frappe.utils.add_to_date(None, hours=-2)
		)
		self.assertIsNone(get_calling_media()["live_exotel_call"])

	def test_a_user_without_exotel_asks_for_no_live_call(self):
		self.make_agent(twilio_number="+15550100001")
		self.enable(twilio=1)
		self.make_exotel_log("t46118-nope", receiver=self.user)
		self.assertIsNone(get_calling_media()["live_exotel_call"])

	def test_only_a_note_or_a_task_links_to_a_call_log(self):
		with self.assertRaises(frappe.ValidationError):
			link_to_call_log("any-sid", "CRM Lead", "any")

	def test_a_call_log_links_to_a_task_whose_name_is_a_number(self):
		call_log = frappe.get_doc(
			doctype="CRM Call Log",
			id="t46116-sid",
			type="Incoming",
			status="In Progress",
			to="+1",
			**{"from": "+2"},
		).insert(ignore_permissions=True)
		task = frappe.get_doc(doctype="CRM Task", title="Follow up").insert(ignore_permissions=True)

		self.assertEqual(link_to_call_log(call_log.name, "CRM Task", str(task.name)), call_log.name)
		self.assertTrue(frappe.get_doc("CRM Call Log", call_log.name).has_link("CRM Task", str(task.name)))

	def test_a_user_without_a_crm_role_cannot_link_a_call_log(self):
		call_log = frappe.get_doc(
			doctype="CRM Call Log",
			id="t46116-denied",
			type="Incoming",
			status="In Progress",
			to="+1",
			**{"from": "+2"},
		).insert(ignore_permissions=True)
		task = frappe.get_doc(doctype="CRM Task", title="Follow up").insert(ignore_permissions=True)
		frappe.set_user(make_user("calling-media-denied-46116@example.com", roles=[]).name)

		with self.assertRaises(frappe.PermissionError):
			link_to_call_log(call_log.name, "CRM Task", str(task.name))
