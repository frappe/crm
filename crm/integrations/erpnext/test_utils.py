import frappe
from frappe.tests.utils import FrappeTestCase


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
