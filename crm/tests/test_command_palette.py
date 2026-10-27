from unittest import TestCase
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.command_palette import ACTIVITY_LIMIT, _get_recent, _search_all, search
from crm.tests import load_crm_user_test_records
from crm.tests.test_search_sqlite import (
	OTHER_SALES_USER,
	SALES_USER,
	CRMSearchForTest,
	add_comment,
	make_deal,
	make_lead,
)


class TestCommandPalette(TestCase):
	@patch("crm.api.command_palette.frappe.get_list")
	@patch("crm.api.command_palette.frappe.has_permission", return_value=True)
	def test_search_returns_matched_fields_as_keywords(self, _has_permission, get_list):
		get_list.side_effect = lambda doctype, **_kwargs: (
			[frappe._dict(name="LEAD-1", lead_name="Jane", organization="Frappe", email=None)]
			if doctype == "CRM Lead"
			else []
		)

		[result] = _search_all("frappe")

		self.assertEqual(result["title"], "Jane")
		self.assertEqual(result["keywords"], "LEAD-1 Jane Frappe")

	@patch("crm.api.command_palette.frappe.get_list")
	@patch("crm.api.command_palette.frappe.has_permission")
	def test_search_skips_doctypes_without_read_permission(self, has_permission, get_list):
		has_permission.side_effect = lambda doctype, _permission: doctype == "CRM Lead"
		get_list.return_value = [frappe._dict(name="LEAD-1", lead_name="Ada")]

		results = _search_all("Ada")

		self.assertEqual([result["doctype"] for result in results], ["CRM Lead"])
		self.assertEqual(get_list.call_count, 1)

	@patch("crm.api.command_palette.frappe.get_list")
	@patch("crm.api.command_palette.frappe.has_permission", return_value=True)
	def test_recents_preserve_the_users_order(self, _has_permission, get_list):
		get_list.return_value = [
			frappe._dict(name="LEAD-1", lead_name="First"),
			frappe._dict(name="LEAD-2", lead_name="Second"),
		]

		results = _get_recent({"CRM Lead": ["LEAD-2", "LEAD-1"]})

		self.assertEqual([result["name"] for result in results], ["LEAD-2", "LEAD-1"])

	@patch("crm.api.command_palette._get_recent")
	@patch("crm.api.command_palette.frappe.parse_json", side_effect=ValueError)
	def test_invalid_recent_payload_is_ignored(self, _parse_json, get_recent):
		get_recent.return_value = []

		result = search(recent_names="not-json")

		self.assertEqual(result["recent"], [])
		get_recent.assert_called_once_with({})


class TestCommandPaletteActivity(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		load_crm_user_test_records()
		cls.own_lead = make_lead(SALES_USER)
		cls.other_lead = make_lead(OTHER_SALES_USER)
		cls.converted_lead = make_lead(SALES_USER)
		cls.deal = make_deal(SALES_USER, lead=cls.converted_lead)
		cls.hidden_source_lead = make_lead(OTHER_SALES_USER)
		make_deal(SALES_USER, lead=cls.hidden_source_lead)
		cls.lead_with_hidden_deal = make_lead(SALES_USER)
		make_deal(OTHER_SALES_USER, lead=cls.lead_with_hidden_deal)

		cls.own_comment = add_comment("CRM Lead", cls.own_lead, "ownleadmarker")
		add_comment("CRM Lead", cls.other_lead, "otherleadmarker")
		cls.converted_comment = add_comment("CRM Lead", cls.converted_lead, "convertedmarker")
		add_comment("CRM Lead", cls.lead_with_hidden_deal, "hiddendealmarker")
		add_comment("CRM Lead", cls.hidden_source_lead, "hiddenleadmarker")
		cls.merged_comment = add_comment("CRM Lead", cls.converted_lead, "mergemarker")
		add_comment("CRM Deal", cls.deal, "mergemarker")
		for _index in range(ACTIVITY_LIMIT + 1):
			add_comment("CRM Lead", make_lead(SALES_USER), "capmarker")

		cls.index = CRMSearchForTest()
		cls.index.drop_index()
		cls.index.build_index()

	@classmethod
	def tearDownClass(cls):
		cls.index.drop_index()
		super().tearDownClass()

	def setUp(self):
		patcher = patch("crm.api.command_palette.CRMSearch", CRMSearchForTest)
		patcher.start()
		self.addCleanup(patcher.stop)
		frappe.set_user(SALES_USER)
		self.addCleanup(frappe.set_user, "Administrator")

	def activity(self, query):
		return search(query)["activity"]

	def parents(self, query):
		return [(row["parent_doctype"], row["parent_name"]) for row in self.activity(query)]

	def test_comment_on_own_lead_is_returned_with_its_record(self):
		[row] = self.activity("ownleadmarker")

		self.assertEqual(
			row,
			{
				"source_doctype": "Comment",
				"source_name": self.own_comment,
				"parent_doctype": "CRM Lead",
				"parent_name": self.own_lead,
				"parent_title": "Search",
				"title": "",
				"snippet": row["snippet"],
				"route": "Lead",
				"route_name": self.own_lead,
				"hash": self.own_comment,
			},
		)
		self.assertIn("<mark>ownleadmarker</mark>", row["snippet"])

	def test_comment_on_another_users_lead_is_hidden(self):
		self.assertEqual(self.activity("otherleadmarker"), [])

	def test_post_filter_keeps_readable_hits_and_drops_the_rest(self):
		with patch("crm.search_sqlite.PREFILTER_LIMIT", 0):
			self.assertEqual(self.parents("ownleadmarker"), [("CRM Lead", self.own_lead)])
			self.assertEqual(self.parents("convertedmarker"), [("CRM Deal", self.deal)])
			self.assertEqual(self.parents("hiddendealmarker"), [("CRM Lead", self.lead_with_hidden_deal)])
			self.assertEqual(self.activity("otherleadmarker"), [])

	def test_unreadable_lead_comment_is_hidden_even_when_its_deal_is_readable(self):
		self.assertEqual(self.activity("hiddenleadmarker"), [])

	def test_post_filter_hides_unreadable_lead_comment_even_when_its_deal_is_readable(self):
		with patch("crm.search_sqlite.PREFILTER_LIMIT", 0):
			self.assertEqual(self.activity("hiddenleadmarker"), [])

	def test_converted_lead_comment_opens_its_deal(self):
		[row] = self.activity("convertedmarker")

		self.assertEqual((row["parent_doctype"], row["parent_name"]), ("CRM Deal", self.deal))
		self.assertEqual((row["route"], row["parent_title"]), ("Deal", "Search Org"))
		self.assertEqual(row["source_name"], self.converted_comment)

	def test_converted_lead_comment_falls_back_to_the_lead_when_its_deal_is_hidden(self):
		self.assertEqual(self.parents("hiddendealmarker"), [("CRM Lead", self.lead_with_hidden_deal)])

	def test_lead_and_deal_hits_for_the_same_deal_merge(self):
		self.assertEqual(self.parents("mergemarker"), [("CRM Deal", self.deal)])

	def test_activity_is_capped(self):
		self.assertEqual(len(self.activity("capmarker")), ACTIVITY_LIMIT)

	def test_missing_index_returns_no_activity(self):
		with patch.object(CRMSearchForTest, "index_exists", return_value=False):
			result = search("ownleadmarker")

		self.assertEqual(result["activity"], [])

	def test_short_query_skips_the_index(self):
		with patch("crm.api.command_palette.CRMSearch") as crm_search:
			self.assertEqual(search("o")["activity"], [])
			self.assertEqual(search("")["activity"], [])

		crm_search.assert_not_called()
