# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from crm.api import dialer as D


class TestDialer(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def make_leads(self, n=3, status=None):
		leads = []
		for i in range(n):
			payload = {
				"doctype": "CRM Lead",
				"first_name": f"Dial{i}",
				"mobile_no": f"+3933300000{i:02d}",
			}
			if status:
				payload["status"] = status
			leads.append(frappe.get_doc(payload).insert())
		return leads

	def test_create_session_builds_queue(self):
		self.make_leads(3)
		session = D.create_session(doctype="CRM Lead", limit=10)
		self.assertGreaterEqual(session["total"], 3)
		self.assertEqual(session["done"], 0)
		self.assertIsNotNone(session["current"])
		self.assertEqual(session["status"], "In Progress")

	def test_only_one_active_session_per_agent(self):
		self.make_leads(2)
		D.create_session(doctype="CRM Lead", limit=5)
		with self.assertRaises(frappe.ValidationError):
			D.create_session(doctype="CRM Lead", limit=5)

	def test_complete_entry_advances_and_logs(self):
		self.make_leads(2)
		session = D.create_session(doctype="CRM Lead", limit=2)
		first = session["current"]
		updated = D.complete_entry(
			session=session["name"], idx=first["idx"], disposition="Interested", note="richiamare"
		)
		self.assertEqual(updated["done"], 1)
		self.assertNotEqual(updated["current"]["idx"], first["idx"])
		comments = frappe.get_all(
			"Comment",
			filters={"reference_doctype": "CRM Lead", "reference_name": first["reference_name"]},
			pluck="content",
		)
		self.assertTrue(any("Interested" in c for c in comments))

	def test_completing_all_entries_completes_session(self):
		self.make_leads(1)
		session = D.create_session(doctype="CRM Lead", limit=1)
		updated = D.complete_entry(session=session["name"], idx=session["current"]["idx"], skipped=True)
		self.assertEqual(updated["status"], "Completed")
		self.assertIsNone(updated["current"])

	def test_end_session(self):
		self.make_leads(1)
		session = D.create_session(doctype="CRM Lead", limit=1)
		ended = D.end_session(session=session["name"], cancel=True)
		self.assertEqual(ended["status"], "Cancelled")
		self.assertIsNone(D.get_active_session())
