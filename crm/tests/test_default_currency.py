import frappe
from frappe.tests import IntegrationTestCase

from crm.install import set_default_currency
from crm.utils import get_base_currency


class TestDefaultCurrency(IntegrationTestCase):
	def setUp(self):
		self.original_crm_currency = frappe.db.get_single_value("FCRM Settings", "currency")
		self.original_system_currency = frappe.db.get_single_value("System Settings", "currency")

	def tearDown(self):
		frappe.db.set_single_value("FCRM Settings", "currency", self.original_crm_currency or "")
		frappe.db.set_single_value("System Settings", "currency", self.original_system_currency or "")

	def test_base_currency_falls_back_to_system_settings(self):
		frappe.db.set_single_value("FCRM Settings", "currency", "")
		frappe.db.set_single_value("System Settings", "currency", "EUR")
		self.assertEqual(get_base_currency(), "EUR")

	def test_base_currency_falls_back_to_usd(self):
		frappe.db.set_single_value("FCRM Settings", "currency", "")
		frappe.db.set_single_value("System Settings", "currency", "")
		self.assertEqual(get_base_currency(), "USD")

	def test_base_currency_prefers_crm_setting(self):
		frappe.db.set_single_value("FCRM Settings", "currency", "GBP")
		frappe.db.set_single_value("System Settings", "currency", "EUR")
		self.assertEqual(get_base_currency(), "GBP")

	def test_set_default_currency_seeds_from_system_settings(self):
		frappe.db.set_single_value("FCRM Settings", "currency", "")
		frappe.db.set_single_value("System Settings", "currency", "EUR")
		set_default_currency()
		self.assertEqual(frappe.db.get_single_value("FCRM Settings", "currency"), "EUR")

	def test_set_default_currency_does_not_override_existing(self):
		frappe.db.set_single_value("FCRM Settings", "currency", "GBP")
		frappe.db.set_single_value("System Settings", "currency", "EUR")
		set_default_currency()
		self.assertEqual(frappe.db.get_single_value("FCRM Settings", "currency"), "GBP")

	def test_set_default_currency_skips_when_system_currency_missing(self):
		frappe.db.set_single_value("FCRM Settings", "currency", "")
		frappe.db.set_single_value("System Settings", "currency", "")
		set_default_currency()
		self.assertFalse(frappe.db.get_single_value("FCRM Settings", "currency"))
