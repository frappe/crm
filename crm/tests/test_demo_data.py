import json
import os

import frappe
from frappe.tests.utils import FrappeTestCase


class TestDemoData(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		from crm.demo.api import clear_demo_data

		clear_demo_data()

	def _check_demo_records_exist(self, doctype, record_names):
		"""Helper method to check if specific demo records exist"""
		if not record_names:
			return False
		for name in record_names:
			if frappe.db.exists(doctype, name):
				return True
		return False

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

		# Check that demo data defaults are not set
		self.assertIsNone(frappe.db.get_default(DEMO_LEADS_KEY))
		self.assertIsNone(frappe.db.get_default(DEMO_NOTES_KEY))
		self.assertIsNone(frappe.db.get_default(DEMO_TASKS_KEY))
		self.assertIsNone(frappe.db.get_default(DEMO_CALL_LOGS_KEY))
		self.assertIsNone(frappe.db.get_default(DEMO_DEALS_KEY))

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

		# Leads - check that demo leads were created
		demo_lead_names = json.loads(frappe.db.get_default(DEMO_LEADS_KEY) or "[]")
		self.assertEqual(len(demo_lead_names), 12)
		for lead_name in demo_lead_names:
			lead = frappe.get_doc("CRM Lead", lead_name)
			self.assertTrue(lead.first_name)
			self.assertTrue(lead.organization)

		# Notes, Tasks, Call Logs, Activities, Deals - check that demo data was created
		demo_note_names = json.loads(frappe.db.get_default(DEMO_NOTES_KEY) or "[]")
		demo_task_names = json.loads(frappe.db.get_default(DEMO_TASKS_KEY) or "[]")
		demo_call_log_names = json.loads(frappe.db.get_default(DEMO_CALL_LOGS_KEY) or "[]")
		demo_deal_data = json.loads(frappe.db.get_default(DEMO_DEALS_KEY) or "{}")

		self.assertGreater(len(demo_note_names), 0)
		self.assertGreater(len(demo_task_names), 0)
		self.assertGreater(len(demo_call_log_names), 0)
		if isinstance(demo_deal_data, dict):
			self.assertGreater(len(demo_deal_data.get("deals", [])), 0)

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

		# 3. Capture demo record names before clearing
		lead_names = json.loads(frappe.db.get_default(DEMO_LEADS_KEY) or "[]")
		note_names = json.loads(frappe.db.get_default(DEMO_NOTES_KEY) or "[]")
		task_names = json.loads(frappe.db.get_default(DEMO_TASKS_KEY) or "[]")
		call_log_names = json.loads(frappe.db.get_default(DEMO_CALL_LOGS_KEY) or "[]")
		deal_data = json.loads(frappe.db.get_default(DEMO_DEALS_KEY) or "{}")

		# Clear demo data
		clear_demo_data()

		# All demo data should be gone - check using the tracked record names

		# Users should be deleted
		for user in DEMO_USERS:
			self.assertFalse(frappe.db.exists("User", user["email"]))

		# Demo records should not exist
		self.assertFalse(self._check_demo_records_exist("CRM Lead", lead_names))
		self.assertFalse(self._check_demo_records_exist("FCRM Note", note_names))
		self.assertFalse(self._check_demo_records_exist("CRM Task", task_names))
		self.assertFalse(self._check_demo_records_exist("CRM Call Log", call_log_names))
		if isinstance(deal_data, dict) and deal_data.get("deals"):
			self.assertFalse(self._check_demo_records_exist("CRM Deal", deal_data.get("deals", [])))

		# Site defaults cleared
		self.assertIsNone(frappe.db.get_default(DEMO_STATE_KEY))
		self.assertIsNone(frappe.db.get_default(DEMO_LEADS_KEY))
		self.assertIsNone(frappe.db.get_default(DEMO_NOTES_KEY))
		self.assertIsNone(frappe.db.get_default(DEMO_TASKS_KEY))
		self.assertIsNone(frappe.db.get_default(DEMO_CALL_LOGS_KEY))
		self.assertIsNone(frappe.db.get_default(DEMO_ACTIVITIES_KEY))
		self.assertIsNone(frappe.db.get_default(DEMO_DEALS_KEY))
