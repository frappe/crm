# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.tests.utils import FrappeTestCase

from crm.www.crm import get_boot, get_layout_direction, is_rtl_language


class TestRtl(FrappeTestCase):
	def test_arabic_hebrew_persian_pashto_are_rtl(self):
		for lang in ("ar", "he", "fa", "ps"):
			self.assertTrue(is_rtl_language(lang))
			self.assertEqual(get_layout_direction(lang), "rtl")

	def test_english_is_ltr(self):
		self.assertFalse(is_rtl_language("en"))
		self.assertEqual(get_layout_direction("en"), "ltr")

	def test_region_suffix_still_rtl(self):
		self.assertEqual(get_layout_direction("ar-SA"), "rtl")

	def test_boot_includes_lang(self):
		boot = get_boot()
		self.assertIn("lang", boot)
		self.assertTrue(boot["lang"])
		self.assertEqual(boot["layout_direction"], get_layout_direction(boot["lang"]))
