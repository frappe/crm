import os

import frappe
from frappe.tests import IntegrationTestCase


class TestDemoData(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		from crm.demo.api import clear_demo_data

		clear_demo_data()

	def test_demo_data_lifecycle(self):
		from crm.demo.api import clear_demo_data, create_demo_data
		from crm.demo.users import DEMO_USERS

		DEMO_STATE_KEY = "crm_demo_data_created"
		DEMO_LEADS_KEY = "crm_demo_leads"
		DEMO_NOTES_KEY = "crm_demo_notes"
		DEMO_TASKS_KEY = "crm_demo_tasks"
		DEMO_CALL_LOGS_KEY = "crm_demo_call_logs"
		DEMO_ACTIVITIES_KEY = "crm_demo_activities"
		DEMO_DEALS_KEY = "crm_demo_deals"

		# 1. Before creation: nothing should exist
		for user in DEMO_USERS:
			self.assertFalse(frappe.db.exists("User", user["email"]))
		self.assertEqual(frappe.db.count("CRM Lead"), 0)
		self.assertEqual(frappe.db.count("FCRM Note"), 0)
		self.assertEqual(frappe.db.count("CRM Task"), 0)
		self.assertEqual(frappe.db.count("CRM Call Log"), 0)
		self.assertEqual(frappe.db.count("CRM Deal"), 0)

		# 2. Create demo data
		create_demo_data()

		# Users
		for user in DEMO_USERS:
			doc = frappe.get_doc("User", user["email"])
			self.assertIsNotNone(doc)
			self.assertEqual(doc.user_image, user["avatar"])
			self.assertTrue(doc.enabled)
			self.assertEqual(doc.first_name, user["first_name"])
			self.assertEqual(doc.last_name, user["last_name"])

		# Leads
		leads = frappe.get_all("CRM Lead", fields=["name", "first_name", "organization", "image"])
		self.assertEqual(len(leads), 12)
		for lead in leads:
			self.assertTrue(lead["first_name"])
			self.assertTrue(lead["organization"])

		# Notes, Tasks, Call Logs, Activities, Deals
		self.assertGreater(frappe.db.count("FCRM Note"), 0)
		self.assertGreater(frappe.db.count("CRM Task"), 0)
		self.assertGreater(frappe.db.count("CRM Call Log"), 0)
		self.assertGreater(frappe.db.count("CRM Deal"), 0)

		# Avatars exist
		avatar_dir = os.path.abspath(
			os.path.join(os.path.dirname(__file__), "..", "..", "crm", "public", "images", "demo")
		)
		for user in DEMO_USERS:
			filename = user["avatar"].split("/")[-1]
			path = os.path.join(avatar_dir, filename)
			self.assertTrue(os.path.exists(path), f"Missing avatar: {path}")

		# Site defaults set
		self.assertEqual(frappe.db.get_default(DEMO_STATE_KEY), "1")
		self.assertTrue(frappe.db.get_default(DEMO_LEADS_KEY))
		self.assertTrue(frappe.db.get_default(DEMO_NOTES_KEY))
		self.assertTrue(frappe.db.get_default(DEMO_TASKS_KEY))
		self.assertTrue(frappe.db.get_default(DEMO_CALL_LOGS_KEY))
		self.assertTrue(frappe.db.get_default(DEMO_ACTIVITIES_KEY))
		self.assertTrue(frappe.db.get_default(DEMO_DEALS_KEY))

		# 3. Clear demo data
		clear_demo_data()

		# All data should be gone
		for user in DEMO_USERS:
			self.assertFalse(frappe.db.exists("User", user["email"]))
		self.assertEqual(frappe.db.count("CRM Lead"), 0)
		self.assertEqual(frappe.db.count("FCRM Note"), 0)
		self.assertEqual(frappe.db.count("CRM Task"), 0)
		self.assertEqual(frappe.db.count("CRM Call Log"), 0)
		self.assertEqual(frappe.db.count("CRM Deal"), 0)
		# Site defaults cleared
		self.assertIsNone(frappe.db.get_default(DEMO_STATE_KEY))
		self.assertIsNone(frappe.db.get_default(DEMO_LEADS_KEY))
		self.assertIsNone(frappe.db.get_default(DEMO_NOTES_KEY))
		self.assertIsNone(frappe.db.get_default(DEMO_TASKS_KEY))
		self.assertIsNone(frappe.db.get_default(DEMO_CALL_LOGS_KEY))
		self.assertIsNone(frappe.db.get_default(DEMO_ACTIVITIES_KEY))
		self.assertIsNone(frappe.db.get_default(DEMO_DEALS_KEY))
