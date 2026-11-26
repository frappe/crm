import frappe
from frappe.tests import IntegrationTestCase

from crm.api.doc import get_quick_filters, update_quick_filters


class TestUpdateQuickFilters(IntegrationTestCase):
	"""Only managers change a doctype's quick filters, and only to its own fields."""

	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.delete("CRM Global Settings", {"dt": "CRM Deal", "type": "Quick Filters"})

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_manager_sets_quick_filters(self):
		frappe.set_user("crm.manager@example.com")

		update_quick_filters('["name", "status"]', "[]", "CRM Deal")

		filters = get_quick_filters("CRM Deal", cached=False)
		self.assertEqual([f["fieldname"] for f in filters], ["name", "status"])

	def test_sales_user_cannot_set_quick_filters(self):
		frappe.set_user("crm.user1@example.com")

		with self.assertRaises(frappe.PermissionError):
			update_quick_filters('["status"]', "[]", "CRM Deal")

		self.assertFalse(frappe.db.exists("CRM Global Settings", {"dt": "CRM Deal", "type": "Quick Filters"}))

	def test_unknown_fields_are_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			update_quick_filters('["no_such_field"]', "[]", "CRM Deal")
		with self.assertRaises(frappe.ValidationError):
			update_quick_filters("[]", '["no_such_field"]', "CRM Deal")

	def test_quick_filters_accept_post_only(self):
		self.assertEqual(frappe.allowed_http_methods_for_whitelisted_func[update_quick_filters], ("POST",))
