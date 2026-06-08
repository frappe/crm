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
	def test_standard_rate_present_skips_item_price(self):
		from crm.integrations.erpnext import item

		doc = frappe._dict(name="ITM-A", standard_rate=50, image=None, disabled=0, description="d")
		calls = []
		original = item.get_item_price_rate
		item.get_item_price_rate = lambda code: calls.append(code) or 999
		try:
			data = item._catalogue_data(doc)
		finally:
			item.get_item_price_rate = original
		self.assertEqual(data["standard_rate"], 50)
		self.assertEqual(calls, [])

	def test_null_standard_rate_falls_back_to_item_price(self):
		from crm.integrations.erpnext import item

		doc = frappe._dict(name="ITM-B", standard_rate=None, image=None, disabled=0, description="d")
		original = item.get_item_price_rate
		item.get_item_price_rate = lambda code: 123 if code == "ITM-B" else None
		try:
			data = item._catalogue_data(doc)
		finally:
			item.get_item_price_rate = original
		self.assertEqual(data["standard_rate"], 123)

	def test_get_item_price_rate_queries_latest_selling_price(self):
		from crm.integrations.erpnext import item

		captured = {}
		original = frappe.db.get_value

		def fake_get_value(doctype, filters, fieldname, **kwargs):
			captured.update(doctype=doctype, filters=filters, fieldname=fieldname, kwargs=kwargs)
			return 77

		frappe.db.get_value = fake_get_value
		try:
			rate = item.get_item_price_rate("ITM-C")
		finally:
			frappe.db.get_value = original
		self.assertEqual(rate, 77)
		self.assertEqual(captured["doctype"], "Item Price")
		self.assertEqual(captured["filters"], {"item_code": "ITM-C", "selling": 1})
		self.assertEqual(captured["fieldname"], "price_list_rate")
		self.assertEqual(captured["kwargs"].get("order_by"), "valid_from desc")


class TestCascadeFlag(FrappeTestCase):
	def test_flag_round_trip(self):
		from crm.integrations.erpnext.utils import CASCADE_FLAG, in_cascade

		self.assertFalse(in_cascade())
		frappe.flags[CASCADE_FLAG] = True
		try:
			self.assertTrue(in_cascade())
		finally:
			frappe.flags[CASCADE_FLAG] = False
