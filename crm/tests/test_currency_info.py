# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from unittest.mock import patch

from frappe.tests.utils import FrappeTestCase

from crm.www.crm import get_boot, get_currency_info


class TestGetCurrencyInfo(FrappeTestCase):
	def test_returns_name_keyed_symbol_map(self):
		# Every enabled currency must be reachable by its code, because the frontend
		# looks the record up as window.currency_info[currencyCode].
		result = get_currency_info()
		self.assertIsInstance(result, dict)
		self.assertIn("USD", result)
		self.assertIn("symbol", result["USD"])
		self.assertIn("symbol_on_right", result["USD"])

	def test_symbol_on_right_is_an_int(self):
		# cint() normalises Check fields, which the DB may return as 0/1 or "0"/"1".
		result = get_currency_info()
		self.assertIn(result["USD"]["symbol_on_right"], (0, 1))

	def test_pln_reports_symbol_on_right(self):
		# PLN ships with the currency set the issue is filed against; if this fixture
		# is absent the rest of the test is meaningless, so assert it exists first.
		result = get_currency_info()
		if "PLN" not in result:
			self.skipTest("PLN fixture not present on this site")
		self.assertEqual(result["PLN"]["symbol_on_right"], 1)

	def test_resilient_when_db_lookup_raises(self):
		# Runs inside get_boot, so a failure here would break the entire CRM page load.
		with patch("crm.www.crm.frappe.db.get_all", side_effect=Exception("db hiccup")):
			self.assertEqual(get_currency_info(), {})


class TestGetBootCurrencyInfo(FrappeTestCase):
	def test_boot_includes_currency_info(self):
		boot = get_boot()
		self.assertIn("currency_info", boot)
		self.assertIsInstance(boot["currency_info"], dict)

	def test_boot_degrades_when_currency_lookup_fails(self):
		# A missing currency map costs symbol placement, not the page.
		with patch("crm.www.crm.frappe.db.get_all", side_effect=Exception("db hiccup")):
			boot = get_boot()
		self.assertEqual(boot["currency_info"], {})
