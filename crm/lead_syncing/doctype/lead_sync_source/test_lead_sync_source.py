# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from datetime import datetime, timezone
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.lead_syncing.doctype.lead_sync_source.facebook import FacebookSyncSource

# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]

FACEBOOK = "crm.lead_syncing.doctype.lead_sync_source.facebook"
FORM_ID = "test-form-78913"


class IntegrationTestLeadSyncSource(IntegrationTestCase):
	def setUp(self):
		patcher = patch(f"{FACEBOOK}.get_system_timezone", return_value="Asia/Karachi")
		patcher.start()
		self.addCleanup(patcher.stop)

		frappe.get_doc(
			{
				"doctype": "Facebook Lead Form",
				"id": FORM_ID,
				"form_name": "Test Meta Form",
				"questions": [{"key": "full_name", "mapped_to_crm_field": "first_name"}],
			}
		).insert(ignore_links=True, ignore_mandatory=True)

		with patch(
			"crm.lead_syncing.doctype.lead_sync_source.lead_sync_source.fetch_and_store_pages_from_facebook"
		):
			self.source = frappe.get_doc(
				{
					"doctype": "Lead Sync Source",
					"__newname": "Test Meta Source",
					"type": "Facebook",
					"access_token": "test-token",
					"facebook_lead_form": FORM_ID,
					"enabled": 0,
				}
			).insert(ignore_links=True, ignore_mandatory=True)

	def tearDown(self):
		frappe.db.rollback()

	def sync(self, leads, last_synced_at=None, started_at=datetime(2026, 9, 16, 14, 37)):
		self.source.db_set("last_synced_at", last_synced_at)
		with (
			patch(f"{FACEBOOK}.make_get_request", return_value={"data": leads}) as request,
			patch(f"{FACEBOOK}.now_datetime", return_value=started_at),
		):
			FacebookSyncSource("test-token", FORM_ID, self.source.name).sync()
		return request

	def test_filter_keeps_time_of_day_in_site_time_zone(self):
		request = self.sync([], last_synced_at="2026-09-16 14:37:00")

		filtering = frappe.parse_json(request.call_args.kwargs["params"]["filtering"])
		# 14:37 in Karachi (UTC+5) is 09:37 UTC
		self.assertEqual(filtering[0]["value"], datetime(2026, 9, 16, 9, 37, tzinfo=timezone.utc).timestamp())

	def test_first_sync_fetches_without_filter(self):
		request = self.sync([])

		self.assertNotIn("filtering", request.call_args.kwargs["params"])

	def test_last_synced_at_is_when_the_sync_started(self):
		self.sync([], started_at=datetime(2026, 9, 16, 1, 5))

		self.assertEqual(
			frappe.db.get_value("Lead Sync Source", self.source.name, "last_synced_at"),
			datetime(2026, 9, 16, 1, 5),
		)

	def test_already_imported_lead_is_skipped_without_a_log(self):
		self.sync([meta_lead("111")])
		self.sync([meta_lead("111")])

		self.assertEqual(frappe.db.count("CRM Lead", {"facebook_lead_id": "111"}), 1)
		self.assertFalse(frappe.db.exists("Failed Lead Sync Log", {"source": self.source.name}))

	def test_field_without_values_does_not_stop_the_sync(self):
		lead = meta_lead("222")
		lead["field_data"].append({"name": "inbox_url"})

		self.sync([lead, meta_lead("333")])

		self.assertTrue(frappe.db.exists("CRM Lead", {"facebook_lead_id": "222"}))
		self.assertTrue(frappe.db.exists("CRM Lead", {"facebook_lead_id": "333"}))


def meta_lead(lead_id):
	return {
		"id": lead_id,
		"created_time": "2026-09-16T01:08:36+0500",
		"field_data": [{"name": "full_name", "values": [f"Meta Lead {lead_id}"]}],
	}
