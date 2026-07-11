import unittest
from importlib.util import find_spec

import frappe
from frappe.tests.utils import FrappeTestCase

# These exercise ERPNext's pricing API; skip when erpnext isn't importable.
ERPNEXT_INSTALLED = find_spec("erpnext") is not None


@unittest.skipUnless(ERPNEXT_INSTALLED, "erpnext not installed")
class TestGetDealProductRate(FrappeTestCase):
	def _fake_get_item_price(self, captured, result):
		from erpnext.stock import get_item_details

		def fake(pctx, item_code, **kwargs):
			captured.update(pctx=dict(pctx), item_code=item_code)
			return result

		orig = get_item_details.get_item_price
		get_item_details.get_item_price = fake
		self.addCleanup(setattr, get_item_details, "get_item_price", orig)

	def _fake_stock_uom(self, uom):
		orig = frappe.db.get_value

		def fake(doctype, filters=None, fieldname="name", *a, **k):
			if doctype == "Item" and fieldname == "stock_uom":
				return uom
			return orig(doctype, filters, fieldname, *a, **k)

		frappe.db.get_value = fake
		self.addCleanup(setattr, frappe.db, "get_value", orig)

	def _fake_price_list(self, value):
		from crm.fcrm.doctype.crm_products import crm_products

		orig = crm_products._resolve_price_list
		crm_products._resolve_price_list = lambda customer: value
		self.addCleanup(setattr, crm_products, "_resolve_price_list", orig)

	def test_passes_price_list_uom_and_date_context(self):
		from crm.fcrm.doctype.crm_products import crm_products

		captured = {}
		self._fake_get_item_price(captured, [frappe._dict(price_list_rate=1021, uom="Nos")])
		self._fake_stock_uom("Nos")
		self._fake_price_list("_Test Price List 2")

		rate = crm_products.get_deal_product_rate("ITM")

		self.assertEqual(rate, 1021)
		self.assertEqual(captured["item_code"], "ITM")
		self.assertEqual(captured["pctx"]["price_list"], "_Test Price List 2")
		self.assertEqual(captured["pctx"]["uom"], "Nos")
		self.assertIn("transaction_date", captured["pctx"])

	def test_returns_none_when_no_matching_price(self):
		from crm.fcrm.doctype.crm_products import crm_products

		self._fake_get_item_price({}, [])
		self._fake_stock_uom("Nos")
		self._fake_price_list("Standard Selling")

		self.assertIsNone(crm_products.get_deal_product_rate("ITM"))

	def test_returns_none_without_price_list(self):
		from crm.fcrm.doctype.crm_products import crm_products

		self._fake_price_list(None)
		self.assertIsNone(crm_products.get_deal_product_rate("ITM"))


@unittest.skipUnless(ERPNEXT_INSTALLED, "erpnext not installed")
class TestGetProductRateDetails(FrappeTestCase):
	def _fake_contextual_rate(self, value):
		from crm.fcrm.doctype.crm_products import crm_products

		orig = crm_products._contextual_rate
		crm_products._contextual_rate = lambda product_code, deal: value
		self.addCleanup(setattr, crm_products, "_contextual_rate", orig)

	def _fake_product(self, product_name, standard_rate):
		orig = frappe.db.get_value

		def fake(doctype, filters=None, fieldname="name", *a, **k):
			if doctype == "CRM Product":
				return frappe._dict(product_name=product_name, standard_rate=standard_rate)
			return orig(doctype, filters, fieldname, *a, **k)

		frappe.db.get_value = fake
		self.addCleanup(setattr, frappe.db, "get_value", orig)

	def test_prefers_contextual_rate(self):
		from crm.fcrm.doctype.crm_products import crm_products

		self._fake_product("Widget", 90)
		self._fake_contextual_rate(1021)

		out = crm_products.get_product_rate_details("CRM-1001", deal="D-1")

		self.assertEqual(out["rate"], 1021)
		self.assertEqual(out["product_name"], "Widget")

	def test_falls_back_to_standard_rate(self):
		from crm.fcrm.doctype.crm_products import crm_products

		self._fake_product("Widget", 90)
		self._fake_contextual_rate(None)

		out = crm_products.get_product_rate_details("CRM-1001")

		self.assertEqual(out["rate"], 90)
