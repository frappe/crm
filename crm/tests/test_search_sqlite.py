import sqlite3
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.search_sqlite import CRMSearch
from crm.tests import load_crm_user_test_records

SALES_USER = "crm.user1@example.com"
OTHER_SALES_USER = "crm.user2@example.com"
FILLER = "lorem ipsum dolor " * 10


class CRMSearchForTest(CRMSearch):
	INDEX_NAME = "test_crm_search.db"


class TestCRMSearch(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		load_crm_user_test_records()
		cls.own_lead = make_lead(SALES_USER)
		cls.source_lead = make_lead(OTHER_SALES_USER)
		cls.other_lead = make_lead(OTHER_SALES_USER)
		cls.deal = make_deal(SALES_USER, lead=cls.source_lead)

		cls.comment = add_comment("CRM Lead", cls.own_lead, f"{FILLER} commentmarker")
		cls.note = add_note("CRM Lead", cls.own_lead, f"{FILLER} notemarker")
		cls.email = add_email("CRM Lead", cls.own_lead, f"<p>{FILLER} emailmarker</p>")
		add_comment("CRM Lead", cls.other_lead, "otherleadmarker")
		add_comment("CRM Lead", cls.source_lead, "sourceleadmarker")

		add_email(
			"CRM Lead",
			cls.own_lead,
			"<p>Sounds good</p><div class='gmail_quote'>On Monday Ada wrote:"
			"<blockquote>gmailquotemarker</blockquote></div>",
		)
		add_email(
			"CRM Lead",
			cls.own_lead,
			"Sounds good\n\nOn Mon, Jan 5, 2026 at 10:00 AM Ada <ada@example.com> wrote:\n"
			"> plainquotemarker",
		)

		todo = frappe.get_doc({"doctype": "ToDo", "description": "Unrelated"}).insert()
		cls.excluded = [
			("Comment", add_comment("CRM Lead", cls.own_lead, "excludedmarker", comment_type="Info")),
			(
				"Communication",
				add_email("CRM Lead", cls.own_lead, "excludedmarker", communication_type="Automated Message"),
			),
			(
				"Communication",
				add_email("CRM Lead", cls.own_lead, "excludedmarker", communication_medium="Phone"),
			),
		]
		cls.other_doctype_rows = [
			("Comment", add_comment("ToDo", todo.name, "otherdoctypemarker")),
			("FCRM Note", add_note("ToDo", todo.name, "otherdoctypemarker")),
			("Communication", add_email("ToDo", todo.name, "otherdoctypemarker")),
		]

		cls.search = CRMSearchForTest()
		cls.search.drop_index()
		cls.search.build_index()

	@classmethod
	def tearDownClass(cls):
		cls.search.drop_index()
		super().tearDownClass()

	def setUp(self):
		frappe.set_user(SALES_USER)
		self.addCleanup(frappe.set_user, "Administrator")

	def hit_ids(self, query):
		return [hit["id"] for hit in self.search.search(query)["results"]]

	def test_comment_note_and_email_match_text_past_the_first_100_characters(self):
		self.assertEqual(self.hit_ids("commentmarker"), [f"Comment:{self.comment}"])
		self.assertEqual(self.hit_ids("notemarker"), [f"FCRM Note:{self.note}"])
		self.assertEqual(self.hit_ids("emailmarker"), [f"Communication:{self.email}"])

	def test_hit_carries_its_parent_record(self):
		[hit] = self.search.search("commentmarker")["results"]

		self.assertEqual(hit["parent"], f"CRM Lead:{self.own_lead}")
		self.assertIn("<mark>commentmarker</mark>", hit["content"])

	def test_email_does_not_match_text_only_in_its_quoted_reply(self):
		self.assertEqual(self.hit_ids("gmailquotemarker"), [])
		self.assertEqual(self.hit_ids("plainquotemarker"), [])
		self.assertEqual(len(self.hit_ids("sounds good")), 2)

	def test_automated_and_non_email_communications_and_non_comment_comments_are_not_indexed(self):
		frappe.set_user("Administrator")

		self.assertEqual(self.hit_ids("excludedmarker"), [])
		self.assert_rejected_when_queued(self.excluded)

	def test_rows_on_other_doctypes_are_not_indexed(self):
		frappe.set_user("Administrator")

		self.assertEqual(self.hit_ids("otherdoctypemarker"), [])
		self.assert_rejected_when_queued(self.other_doctype_rows)

	def assert_rejected_when_queued(self, rows):
		"""The index queue loads rows by name, bypassing the build's filters."""
		for doctype, name in rows:
			self.assertIsNone(self.search.prepare_document(frappe.get_doc(doctype, name)))

	def test_search_filters_are_the_readable_leads_and_deals(self):
		parents = self.search.get_search_filters()["parent"]

		self.assertFalse(self.search.is_post_filter_required)
		self.assertIn(f"CRM Lead:{self.own_lead}", parents)
		self.assertIn(f"CRM Deal:{self.deal}", parents)
		self.assertNotIn(f"CRM Lead:{self.other_lead}", parents)
		self.assertEqual(self.hit_ids("otherleadmarker"), [])

	def test_search_filters_leave_out_an_unreadable_source_lead_of_a_readable_deal(self):
		parents = self.search.get_search_filters()["parent"]

		self.assertIn(f"CRM Deal:{self.deal}", parents)
		self.assertNotIn(f"CRM Lead:{self.source_lead}", parents)
		self.assertEqual(self.hit_ids("sourceleadmarker"), [])

	def test_too_many_readable_records_switch_to_post_filtering(self):
		with patch("crm.search_sqlite.PREFILTER_LIMIT", 0):
			self.assertEqual(self.search.get_search_filters(), {})

		self.assertTrue(self.search.is_post_filter_required)

	def test_index_write_errors_do_not_break_a_comment_insert(self):
		locked = sqlite3.OperationalError("database is locked")
		with (
			patch("frappe.search.sqlite_search.get_search_classes", return_value=[CRMSearchForTest]),
			patch.object(CRMSearchForTest, "add_to_queue", side_effect=locked),
			patch.object(CRMSearchForTest, "sql", side_effect=locked),
		):
			name = add_comment("CRM Lead", self.own_lead, "lockedmarker")
			self.search.index_doc("Comment", name)
			self.search.remove_doc("Comment", name)

		self.assertTrue(frappe.db.exists("Comment", name))


def make_lead(owner):
	doc = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Search", "lead_owner": owner})
	return doc.insert(ignore_permissions=True).name


def make_deal(owner, lead):
	doc = frappe.get_doc(
		{"doctype": "CRM Deal", "deal_owner": owner, "organization": "Search Org", "lead": lead}
	)
	doc.flags.ignore_mandatory = True
	doc.flags.ignore_links = True
	return doc.insert(ignore_permissions=True).name


def add_comment(doctype, name, content, comment_type="Comment"):
	doc = frappe.get_doc(
		{
			"doctype": "Comment",
			"comment_type": comment_type,
			"comment_email": SALES_USER,
			"reference_doctype": doctype,
			"reference_name": name,
			"content": content,
		}
	)
	return doc.insert(ignore_permissions=True).name


def add_note(doctype, name, content):
	doc = frappe.get_doc(
		{
			"doctype": "FCRM Note",
			"title": "Call notes",
			"content": content,
			"reference_doctype": doctype,
			"reference_docname": name,
		}
	)
	return doc.insert(ignore_permissions=True).name


def add_email(doctype, name, content, communication_type="Communication", communication_medium="Email"):
	doc = frappe.get_doc(
		{
			"doctype": "Communication",
			"communication_type": communication_type,
			"communication_medium": communication_medium,
			"sent_or_received": "Received",
			"sender": "ada@example.com",
			"subject": "Pricing",
			"content": content,
			"reference_doctype": doctype,
			"reference_name": name,
		}
	)
	return doc.insert(ignore_permissions=True).name
