# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.exceptions import FrappeTypeError
from frappe.tests import IntegrationTestCase

from crm.api.onboarding import get_first_deal, get_first_lead

SALES_USER = "onboarding-rep@example.com"


class TestOnboardingAPI(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not frappe.db.exists("User", SALES_USER):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": SALES_USER,
					"first_name": "Onboarding Rep",
					"send_welcome_email": 0,
				}
			).insert(ignore_permissions=True)
			user.add_roles("Sales User")

	def setUp(self):
		frappe.db.savepoint("test_onboarding")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback(save_point="test_onboarding")
		super().tearDown()

	def _make_lead(self, email, owner=None):
		lead = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Test", "email": email, "lead_owner": owner}
		)
		lead.insert(ignore_permissions=True)
		return lead

	def _make_deal(self):
		deal = frappe.get_doc({"doctype": "CRM Deal", "organization": None})
		deal.insert(ignore_permissions=True)
		return deal

	# ---- get_first_deal ----

	def test_get_first_deal_keeps_cached_deal_that_exists(self):
		self._make_deal()
		cached = self._make_deal()
		# the cached deal wins even though it is not the oldest
		self.assertEqual(get_first_deal(name=cached.name), cached.name)

	def test_get_first_deal_falls_back_when_cached_deal_is_deleted(self):
		"""A stale id (deal deleted after being cached client-side) must not be echoed back."""
		self._make_deal()
		cached = self._make_deal()
		frappe.delete_doc("CRM Deal", cached.name, ignore_permissions=True, force=True)
		first = get_first_deal(name=cached.name)
		self.assertNotEqual(first, cached.name)
		self.assertTrue(frappe.db.exists("CRM Deal", first))

	def test_get_first_deal_returns_none_when_no_deals(self):
		frappe.db.delete("CRM Deal")
		self.assertIsNone(get_first_deal(name="CRM-DEAL-DOES-NOT-EXIST"))

	def test_get_first_deal_rejects_non_string_name(self):
		"""A list/dict would be read as a filter by the db layer; the type check must reject it."""
		self._make_deal()
		with self.assertRaises(FrappeTypeError):
			get_first_deal(name=["like", "%"])
		with self.assertRaises(FrappeTypeError):
			get_first_deal(name={"name": ["like", "%"]})

	# ---- get_first_lead ----

	def test_get_first_lead_keeps_cached_lead_that_exists(self):
		self._make_lead("older@example.com")
		cached = self._make_lead("cached@example.com")
		self.assertEqual(get_first_lead(name=cached.name), cached.name)

	def test_get_first_lead_falls_back_when_cached_lead_is_deleted(self):
		self._make_lead("older@example.com")
		cached = self._make_lead("cached@example.com")
		frappe.delete_doc("CRM Lead", cached.name, ignore_permissions=True, force=True)
		first = get_first_lead(name=cached.name)
		self.assertNotEqual(first, cached.name)
		self.assertTrue(frappe.db.exists("CRM Lead", {"name": first, "converted": 0}))

	def test_get_first_lead_falls_back_when_cached_lead_is_converted(self):
		"""The onboarding step opens the lead to convert it, so a converted lead is stale too."""
		self._make_lead("older@example.com")
		cached = self._make_lead("cached@example.com")
		frappe.db.set_value("CRM Lead", cached.name, "converted", 1)
		first = get_first_lead(name=cached.name)
		self.assertNotEqual(first, cached.name)
		self.assertTrue(frappe.db.exists("CRM Lead", {"name": first, "converted": 0}))

	def test_get_first_lead_rejects_non_string_name(self):
		self._make_lead("cached@example.com")
		with self.assertRaises(FrappeTypeError):
			get_first_lead(name=["like", "%"])
		with self.assertRaises(FrappeTypeError):
			get_first_lead(name={"name": ["like", "%"]})

	# ---- permissions ----

	def test_get_first_lead_falls_back_when_user_cannot_read_cached_lead(self):
		"""A Sales User only sees their own / assigned leads; a cached lead they lost access to is stale."""
		someone_elses = self._make_lead("cached@example.com", owner="Administrator")
		mine = self._make_lead("mine@example.com", owner=SALES_USER)

		frappe.set_user(SALES_USER)
		self.assertEqual(get_first_lead(name=someone_elses.name), mine.name)

	def test_get_first_lead_returns_none_when_user_can_read_no_leads(self):
		self._make_lead("cached@example.com", owner="Administrator")

		frappe.set_user(SALES_USER)
		self.assertIsNone(get_first_lead())
