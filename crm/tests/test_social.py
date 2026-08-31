# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from crm.api import social as S
from crm.social.publisher import process_due_posts


def make_account(name="Test FB", platform="Facebook"):
	if frappe.db.exists("CRM Social Account", name):
		return frappe.get_doc("CRM Social Account", name)
	return frappe.get_doc(
		{"doctype": "CRM Social Account", "account_name": name, "platform": platform, "enabled": 1}
	).insert()


class TestSocialPlanner(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_save_requires_content_and_targets(self):
		make_account()
		with self.assertRaises(frappe.ValidationError):
			S.save_post({"content": "hello", "targets": []})
		with self.assertRaises(frappe.ValidationError):
			S.save_post({"content": "  ", "targets": [{"account": "Test FB"}]})

	def test_schedule_requires_datetime(self):
		make_account()
		with self.assertRaises(frappe.ValidationError):
			S.save_post({"content": "ciao", "status": "Scheduled", "targets": [{"account": "Test FB"}]})

	def test_manual_provider_publishes_due_post(self):
		make_account()
		settings = frappe.get_doc("CRM Social Settings")
		settings.provider = "Manual"
		settings.save()

		result = S.save_post(
			{
				"content": "post di prova",
				"status": "Scheduled",
				"scheduled_at": frappe.utils.add_to_date(frappe.utils.now_datetime(), hours=-1),
				"targets": [{"account": "Test FB"}],
			}
		)
		process_due_posts()
		doc = frappe.get_doc("CRM Social Post", result["name"])
		self.assertEqual(doc.status, "Published")
		self.assertEqual(doc.targets[0].status, "Published")
		self.assertTrue(doc.published_at)

	def test_recurrence_clones_next_occurrence(self):
		make_account()
		frappe.get_doc("CRM Social Settings").db_set("provider", "Manual")
		result = S.save_post(
			{
				"content": "ricorrente",
				"status": "Scheduled",
				"recurrence": "Weekly",
				"scheduled_at": frappe.utils.add_to_date(frappe.utils.now_datetime(), hours=-1),
				"targets": [{"account": "Test FB"}],
			}
		)
		process_due_posts()
		clones = frappe.get_all(
			"CRM Social Post", filters={"content": "ricorrente", "status": "Scheduled"}, pluck="name"
		)
		self.assertEqual(len(clones), 1)
		self.assertNotEqual(clones[0], result["name"])

	def test_cancel_post(self):
		make_account()
		result = S.save_post({"content": "bozza", "targets": [{"account": "Test FB"}]})
		S.cancel_post(result["name"])
		self.assertEqual(frappe.db.get_value("CRM Social Post", result["name"], "status"), "Cancelled")
