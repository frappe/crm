# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json
from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.client import set_value
from frappe.tests import IntegrationTestCase, UnitTestCase
from frappe.utils.file_manager import save_file

from crm.api.activities import get_activities, get_file_index, parse_attachment_log


def make_file(name, url, creation, is_private=False):
	return SimpleNamespace(name=name, file_url=url, creation=creation, is_private=is_private)


def make_version(name, old_url, new_url, creation="2026-09-29 10:30:00"):
	return SimpleNamespace(
		docname=name,
		data=json.dumps({"changed": [["file_url", old_url, new_url]]}),
		creation=creation,
	)


def added_log(url, index, creation="2026-09-29 10:00:00"):
	return parse_attachment_log(f'<a href="{url}">invoice.pdf</a>', "Attachment", index, creation)


class TestAttachmentActivities(UnitTestCase):
	@patch("crm.api.activities.frappe.db.get_all")
	def test_privacy_change_resolves_by_file_history_with_duplicate_names(self, get_all):
		old_url = "/private/files/old-blob/invoice.pdf"
		current_url = "/files/new-blob/invoice.pdf"
		files = [
			make_file("original", current_url, "2026-09-29 09:00:00"),
			make_file("other", "/files/other-blob/invoice.pdf", "2026-09-29 09:00:00"),
		]
		get_all.return_value = [make_version("original", old_url, current_url)]

		data = added_log(old_url, get_file_index(files))

		self.assertEqual(data["file_url"], current_url)
		self.assertFalse(data["is_private"])

	@patch("crm.api.activities.frappe.db.get_all")
	def test_deleted_file_does_not_resolve_to_same_named_replacement(self, get_all):
		get_all.return_value = []
		files = [make_file("replacement", "/files/new-blob/invoice.pdf", "2026-09-30 09:00:00")]

		data = added_log("/private/files/old-blob/invoice.pdf", get_file_index(files))

		self.assertEqual(data["file_url"], "")

	@patch("crm.api.activities.frappe.db.get_all")
	def test_reused_url_cannot_rebind_old_log_to_new_file(self, get_all):
		get_all.return_value = []
		url = "/files/invoice.pdf"
		files = [make_file("replacement", url, "2026-09-30 09:00:00")]

		data = added_log(url, get_file_index(files))

		self.assertEqual(data["file_url"], "")

	@patch("crm.api.activities.frappe.db.get_all")
	def test_expired_historical_url_cannot_rebind_later_log(self, get_all):
		old_url = "/private/files/invoice.pdf"
		current_url = "/files/invoice.pdf"
		files = [make_file("earlier", current_url, "2026-09-29 09:00:00")]
		get_all.return_value = [make_version("earlier", old_url, current_url)]

		data = added_log(old_url, get_file_index(files), creation="2026-09-29 11:00:00")

		self.assertEqual(data["file_url"], "")

	@patch("crm.api.activities.frappe.db.get_all")
	def test_shared_historical_url_is_ambiguous(self, get_all):
		old_url = "/private/files/invoice.pdf"
		files = [
			make_file("first", "/files/first.pdf", "2026-09-29 09:00:00"),
			make_file("second", "/files/second.pdf", "2026-09-29 09:00:00"),
		]
		get_all.return_value = [
			make_version("first", old_url, files[0].file_url),
			make_version("second", old_url, files[1].file_url),
		]

		data = added_log(old_url, get_file_index(files))

		self.assertEqual(data["file_url"], "")

	@patch("crm.api.activities.frappe.db.get_all")
	def test_duplicate_upload_sharing_url_remains_clickable(self, get_all):
		get_all.return_value = []
		url = "/files/invoice.pdf"
		files = [
			make_file("first", url, "2026-09-29 09:00:00"),
			make_file("second", url, "2026-09-29 09:30:00"),
		]

		data = added_log(url, get_file_index(files), creation="2026-09-29 09:30:01")

		self.assertEqual(data["file_url"], url)
		self.assertFalse(data["is_private"])

	@patch("crm.api.activities.frappe.db.get_all")
	def test_current_file_url_remains_clickable(self, get_all):
		get_all.return_value = []
		url = "/private/files/invoice.pdf"
		files = [make_file("original", url, "2026-09-29 09:00:00", is_private=True)]

		data = added_log(url, get_file_index(files))

		self.assertEqual(data["file_url"], url)
		self.assertTrue(data["is_private"])


class TestAttachmentActivityPrivacy(IntegrationTestCase):
	def setUp(self):
		frappe.db.savepoint("test_attachment_activity_privacy")

	def tearDown(self):
		frappe.db.rollback(save_point="test_attachment_activity_privacy")

	def assert_privacy_change_updates_activity(self, doctype):
		doc = frappe.get_doc({"doctype": doctype, "first_name": "Attachment"})
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		file = save_file("activity-privacy-test.txt", b"activity test", doctype, doc.name, is_private=1)
		old_url = file.file_url
		# The client API records a Version in production; tests disable versions by default.
		with patch("frappe.in_test", False):
			set_value("File", file.name, {"is_private": 0})
		file.reload()

		self.assertNotEqual(file.file_url, old_url)
		activities, *_ = get_activities(doc.name)
		added = next(
			a["data"]
			for a in activities
			if a["activity_type"] == "attachment_log" and a["data"]["type"] == "added"
		)
		self.assertEqual(added["file_url"], file.file_url)
		self.assertFalse(added["is_private"])

	def test_lead_privacy_change_updates_activity(self):
		self.assert_privacy_change_updates_activity("CRM Lead")

	def test_deal_privacy_change_updates_activity(self):
		self.assert_privacy_change_updates_activity("CRM Deal")

	def test_reused_historical_url_does_not_link_deleted_file_to_earlier_file(self):
		lead = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Attachment"})
		lead.flags.ignore_mandatory = True
		lead.insert(ignore_permissions=True)
		filename = f"activity-reuse-{frappe.generate_hash(length=8)}.txt"
		earlier = save_file(filename, b"earlier content", "CRM Lead", lead.name, is_private=1)
		old_url = earlier.file_url
		with patch("frappe.in_test", False):
			set_value("File", earlier.name, {"is_private": 0})
		# Model a later attachment whose File record has since been deleted.
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Attachment",
				"reference_doctype": "CRM Lead",
				"reference_name": lead.name,
				"content": f'<a href="{old_url}">{filename}</a>',
			}
		).insert(ignore_permissions=True)

		activities, *_ = get_activities(lead.name)
		added = [
			a["data"]
			for a in activities
			if a["activity_type"] == "attachment_log" and a["data"]["type"] == "added"
		]
		self.assertEqual(added[0]["file_url"], "")
