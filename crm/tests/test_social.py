# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from crm.api import social as S
from crm.social.accounts import sync_from_facebook_pages, upsert_account
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

	def test_upsert_account_matches_by_provider_id(self):
		self.assertEqual(upsert_account("Facebook", "111", "Pagina Uno"), "created")
		self.assertEqual(upsert_account("Facebook", "111", "Pagina Uno"), "updated")
		self.assertEqual(
			frappe.db.count("CRM Social Account", {"platform": "Facebook", "provider_account_id": "111"}),
			1,
		)

	def test_sync_from_facebook_pages_creates_fb_and_ig_accounts(self):
		if not frappe.db.exists("Facebook Page", "5550001"):
			frappe.get_doc(
				{
					"doctype": "Facebook Page",
					"id": "5550001",
					"page_name": "Agenzia Demo",
					"instagram_account_id": "17840000001",
					"instagram_username": "agenzia.demo",
				}
			).insert(ignore_permissions=True)

		result = sync_from_facebook_pages()
		self.assertGreaterEqual(result["created"] + result["updated"], 2)
		fb = frappe.db.get_value(
			"CRM Social Account",
			{"platform": "Facebook", "provider_account_id": "5550001"},
			["account_name", "facebook_page"],
			as_dict=True,
		)
		self.assertEqual(fb.account_name, "Agenzia Demo")
		self.assertEqual(fb.facebook_page, "5550001")
		ig = frappe.db.get_value(
			"CRM Social Account",
			{"platform": "Instagram", "provider_account_id": "17840000001"},
			["account_name", "facebook_page"],
			as_dict=True,
		)
		self.assertEqual(ig.account_name, "@agenzia.demo")
		self.assertEqual(ig.facebook_page, "5550001")
		# idempotent
		again = sync_from_facebook_pages()
		self.assertEqual(again["created"], 0)
