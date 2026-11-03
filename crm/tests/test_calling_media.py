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
		self.assertEqual(get_calling_media(), {"media": [], "default_medium": None})

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
