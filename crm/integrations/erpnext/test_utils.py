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


class TestCascadeFlag(FrappeTestCase):
	def test_flag_round_trip(self):
		from crm.integrations.erpnext.utils import CASCADE_FLAG, in_cascade

		self.assertFalse(in_cascade())
		frappe.flags[CASCADE_FLAG] = True
		try:
			self.assertTrue(in_cascade())
		finally:
			frappe.flags[CASCADE_FLAG] = False
