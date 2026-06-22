import frappe
from frappe.tests.utils import FrappeTestCase

# Doctypes whose sync behaviour moved from override_doctype_class to doc_events
SYNC_DOCTYPES = ("Item", "User Permission", "DocShare")


class TestSyncHookWiring(FrappeTestCase):
	def test_sync_doctypes_not_class_overridden(self):
		from crm.hooks import override_doctype_class

		for doctype in SYNC_DOCTYPES:
			self.assertNotIn(doctype, override_doctype_class)

	def test_doc_event_handlers_are_importable(self):
		from crm.hooks import doc_events

		for doctype in SYNC_DOCTYPES:
			for handlers in doc_events[doctype].values():
				for path in handlers:
					self.assertTrue(callable(frappe.get_attr(path)), path)


class TestFindTargetFor(FrappeTestCase):
	def test_returns_none_for_unknown_doctype(self):
		from crm.integrations.erpnext.utils import find_target_for

		self.assertIsNone(find_target_for("Some Other DocType", "X"))

	def test_returns_none_when_inputs_missing(self):
		from crm.integrations.erpnext.utils import find_target_for

		self.assertIsNone(find_target_for(None, "X"))
		self.assertIsNone(find_target_for("Item", None))


class TestItemRateFallback(FrappeTestCase):
	def test_item_price_takes_precedence_over_standard_rate(self):
		from crm.integrations.erpnext import item

		doc = frappe._dict(
			name="ITM-A", stock_uom="Nos", standard_rate=50, image=None, disabled=0, description="d"
		)
		original = item.get_item_price_rate
		item.get_item_price_rate = lambda code, uom=None: 999
		try:
			data = item._catalogue_data(doc)
		finally:
			item.get_item_price_rate = original
		self.assertEqual(data["standard_rate"], 999)

	def test_falls_back_to_standard_rate_when_no_item_price(self):
		from crm.integrations.erpnext import item

		doc = frappe._dict(
			name="ITM-B", stock_uom="Nos", standard_rate=50, image=None, disabled=0, description="d"
		)
		original = item.get_item_price_rate
		item.get_item_price_rate = lambda code, uom=None: None
		try:
			data = item._catalogue_data(doc)
		finally:
			item.get_item_price_rate = original
		self.assertEqual(data["standard_rate"], 50)

	def test_get_item_price_rate_uses_default_price_list_and_general_party(self):
		from erpnext.stock import get_item_details

		from crm.integrations.erpnext import item

		captured = {}
		orig_single = frappe.db.get_single_value
		orig_get_item_price = get_item_details.get_item_price
		frappe.db.get_single_value = lambda doctype, field: "Standard Selling"

		def fake_get_item_price(pctx, item_code, **kwargs):
			captured.update(pctx=dict(pctx), item_code=item_code, kwargs=kwargs)
			return [frappe._dict(name="IP-1", price_list_rate=77, uom="Nos")]

		get_item_details.get_item_price = fake_get_item_price
		try:
			rate = item.get_item_price_rate("ITM-C", "Nos")
		finally:
			frappe.db.get_single_value = orig_single
			get_item_details.get_item_price = orig_get_item_price
		self.assertEqual(rate, 77)
		self.assertEqual(captured["item_code"], "ITM-C")
		self.assertEqual(captured["pctx"]["price_list"], "Standard Selling")
		self.assertEqual(captured["pctx"]["uom"], "Nos")
		self.assertIn("transaction_date", captured["pctx"])
		# No customer/supplier and ignore_party unset -> ERPNext selects general prices only
		self.assertNotIn("customer", captured["pctx"])
		self.assertFalse(captured["kwargs"].get("ignore_party"))

	def test_get_item_price_rate_returns_none_without_default_price_list(self):
		from crm.integrations.erpnext import item

		original = frappe.db.get_single_value
		frappe.db.get_single_value = lambda doctype, field: None
		try:
			self.assertIsNone(item.get_item_price_rate("ITM-X"))
		finally:
			frappe.db.get_single_value = original


class TestCascadeFlag(FrappeTestCase):
	def test_flag_round_trip(self):
		from crm.integrations.erpnext.utils import CASCADE_FLAG, in_cascade

		self.assertFalse(in_cascade())
		frappe.flags[CASCADE_FLAG] = True
		try:
			self.assertTrue(in_cascade())
		finally:
			frappe.flags[CASCADE_FLAG] = False
