# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from contextlib import contextmanager
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.api import contact as C

PROVIDER = "crm.tests.test_contact_tabs.provider"
CALLS = []


def provider(contact, start, page_length):
	"""Stand-in for an app's tab provider: echoes its arguments as rows."""
	CALLS.append({"contact": contact, "start": start, "page_length": page_length})
	return {
		"rows": [
			{
				"name": "R-1",
				"title": f"Row for {contact}",
				"amount": 1234.5,
				"currency": "USD",
				"day": "2026-09-30",
				"url": "/app/contact/x",
			},
			{"name": "R-2", "title": "external", "amount": None, "url": "https://example.com/x"},
			{"name": "R-3", "title": "protocol relative", "url": "//example.com/x"},
			{"name": "R-4", "title": "backslash", "url": "/\\example.com/x"},
			{"name": "R-5", "title": "tab", "url": "/\t/example.com/x"},
			{"name": "R-6", "title": "newline", "url": "/\n/example.com/x"},
			{"name": "R-7", "title": "script", "url": "javascript:alert(1)"},
			{"name": "R-8", "title": "not a string", "url": 42},
		],
		"total_count": 42,
	}


def empty_provider(contact, start, page_length):
	return {"rows": [], "total_count": 0}


TABS = [
	{
		"name": "rows",
		"label": "Rows",
		"icon": "lucide-list",
		"doctype": "Contact",
		"method": PROVIDER,
		"columns": [
			{"label": "Title", "key": "title"},
			{"label": "Amount", "key": "amount", "fieldtype": "Currency"},
			{"label": "Day", "key": "day", "fieldtype": "Date"},
		],
	},
	{
		"name": "errors",
		"label": "Errors",
		"doctype": "Error Log",
		"method": "crm.tests.test_contact_tabs.empty_provider",
		"columns": [],
	},
	# skipped: no method, reserved names, a repeated name, a DocType that does not exist
	{"name": "broken", "label": "Broken"},
	{"name": "Deals", "label": "Deals", "method": PROVIDER},
	{"name": "details", "label": "Details", "method": PROVIDER},
	{"name": "rows", "label": "Rows again", "method": PROVIDER},
	{"name": "ghost", "label": "Ghost", "doctype": "No Such DocType", "method": PROVIDER},
	# kept: columns default to []
	{"name": "bare", "label": "Bare", "method": "crm.tests.test_contact_tabs.empty_provider"},
]


@contextmanager
def contact_tab_hooks(tabs):
	get_hooks = frappe.get_hooks

	def fake(hook=None, *args, **kwargs):
		if hook == "crm_contact_tabs":
			return list(tabs)
		return get_hooks(hook, *args, **kwargs)

	with patch("frappe.get_hooks", side_effect=fake):
		yield


class TestContactTabs(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.contact = frappe.get_doc(
			{"doctype": "Contact", "first_name": "Tabs", "last_name": frappe.generate_hash(length=8)}
		).insert(ignore_permissions=True)
		email = f"no-roles-{frappe.generate_hash(length=8)}@example.com"
		cls.no_roles_user = frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": "No Roles", "user_type": "Website User"}
		).insert(ignore_permissions=True)

	def setUp(self):
		CALLS.clear()

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_no_hooks_gives_no_tabs(self):
		with contact_tab_hooks([]):
			self.assertEqual(C.get_contact_tabs(self.contact.name), [])

	def test_hook_tabs_are_listed_without_method(self):
		with contact_tab_hooks(TABS):
			tabs = C.get_contact_tabs(self.contact.name)
		self.assertEqual([t["name"] for t in tabs], ["rows", "errors", "bare"])
		self.assertNotIn("method", tabs[0])
		self.assertEqual(tabs[0]["label"], "Rows")
		self.assertEqual(tabs[0]["icon"], "lucide-list")
		self.assertEqual(tabs[0]["columns"], TABS[0]["columns"])

	def test_tab_hidden_without_doctype_read(self):
		frappe.set_user("Administrator")
		with (
			contact_tab_hooks(TABS),
			patch.object(
				C.frappe, "has_permission", side_effect=lambda doctype, *a, **k: doctype != "Error Log"
			),
		):
			tabs = C.get_contact_tabs(self.contact.name)
			self.assertEqual([t["name"] for t in tabs], ["rows", "bare"])
			with self.assertRaises(frappe.PermissionError):
				C.get_contact_tab_rows(self.contact.name, "errors")

	def test_invalid_descriptors_are_skipped(self):
		with contact_tab_hooks(TABS):
			tabs = {t["name"]: t for t in C.get_contact_tabs(self.contact.name)}
			# the first "rows" wins over the repeated one
			self.assertEqual(tabs["rows"]["label"], "Rows")
			self.assertEqual(tabs["bare"]["columns"], [])
			for name in ("broken", "Deals", "details", "ghost"):
				self.assertNotIn(name, tabs)
				with self.assertRaises(frappe.DoesNotExistError):
					C.get_contact_tab_rows(self.contact.name, name)

	def test_unknown_doctype_does_not_hide_other_tabs_from_a_user(self):
		# has_permission raises on a DocType that does not exist; the descriptor is dropped first
		frappe.set_user("crm.user1@example.com")
		with contact_tab_hooks(TABS):
			tabs = [t["name"] for t in C.get_contact_tabs(self.contact.name)]
		self.assertIn("rows", tabs)
		self.assertNotIn("ghost", tabs)

	def test_no_contact_read_is_refused(self):
		frappe.set_user(self.no_roles_user.name)
		with contact_tab_hooks(TABS):
			with self.assertRaises(frappe.PermissionError):
				C.get_contact_tabs(self.contact.name)
			with self.assertRaises(frappe.PermissionError):
				C.get_contact_tab_rows(self.contact.name, "rows")
		self.assertEqual(CALLS, [])

	def test_unknown_tab_is_refused(self):
		with contact_tab_hooks(TABS):
			with self.assertRaises(frappe.DoesNotExistError):
				C.get_contact_tab_rows(self.contact.name, "nope")
			# a declared entry without a method is not a tab
			with self.assertRaises(frappe.DoesNotExistError):
				C.get_contact_tab_rows(self.contact.name, "broken")

	def test_rows_forward_paging_and_cap(self):
		with contact_tab_hooks(TABS):
			result = C.get_contact_tab_rows(self.contact.name, "rows", start="20", page_length="20")
			C.get_contact_tab_rows(self.contact.name, "rows", start=-5, page_length=1000)
			C.get_contact_tab_rows(self.contact.name, "rows", page_length=0)
		self.assertEqual(result["total_count"], 42)
		self.assertEqual(
			CALLS,
			[
				{"contact": self.contact.name, "start": 20, "page_length": 20},
				{"contact": self.contact.name, "start": 0, "page_length": C.CONTACT_TAB_MAX_PAGE_LENGTH},
				{"contact": self.contact.name, "start": 0, "page_length": 1},
			],
		)

	def test_rows_are_formatted_by_fieldtype(self):
		with contact_tab_hooks(TABS):
			rows = C.get_contact_tab_rows(self.contact.name, "rows")["rows"]
		first = rows[0]
		self.assertEqual(first["title"], f"Row for {self.contact.name}")
		self.assertEqual(
			first["amount"], frappe.format_value(1234.5, {"fieldtype": "Currency"}, currency="USD")
		)
		self.assertIn("1,234.50", first["amount"])
		self.assertEqual(first["day"], frappe.format_value("2026-09-30", {"fieldtype": "Date"}))
		# untyped and empty values are passed through as they are
		self.assertIsNone(rows[1]["amount"])

	def test_only_same_origin_urls_are_kept(self):
		with contact_tab_hooks(TABS):
			rows = C.get_contact_tab_rows(self.contact.name, "rows")["rows"]
		self.assertEqual(rows[0]["url"], "/app/contact/x")
		for row in rows[1:]:
			self.assertNotIn("url", row, row["title"])

	def test_same_origin_path(self):
		for url in ("/", "/app/order/ORD-1", "/crm/contacts/Ana%20Lopez?tab=1#x"):
			self.assertTrue(C.is_same_origin_path(url), url)
		for url in (
			"",
			None,
			"app/x",
			"//evil.com",
			"/\\evil.com",
			"\\/evil.com",
			"/\t/evil.com",
			"/\n/evil.com",
			"/ x",
			"/\x7f",
			"javascript:alert(1)",
			"https://evil.com",
		):
			self.assertFalse(C.is_same_origin_path(url), repr(url))

	def test_empty_provider(self):
		with contact_tab_hooks(TABS):
			self.assertEqual(
				C.get_contact_tab_rows(self.contact.name, "errors"), {"rows": [], "total_count": 0}
			)
