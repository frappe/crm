import frappe

from crm.api.doc import get_data, get_quick_filters
from crm.install import add_default_quick_filters
from crm.tests import CRMTestCase


class TestListViewColumns(CRMTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.db.rollback()

	def test_data_import_list_uses_crm_defaults(self):
		"""The Data Import page lists a framework doctype, so CRM gives it columns."""
		frappe.db.delete("CRM View Settings", {"dt": "Data Import", "user": "Administrator"})

		result = get_data(
			doctype="Data Import",
			filters={},
			order_by="modified desc",
			page_length=1,
			view={"view_type": "list"},
		)
		keys = [column["key"] for column in result["columns"]]

		self.assertTrue(result["is_default"])
		self.assertEqual(
			keys, ["name", "status", "reference_doctype", "import_type", "import_file", "modified"]
		)
		self.assertIn("google_sheets_url", result["rows"])

	def test_data_import_list_gets_search_and_filters(self):
		"""Data Import has no standard filters, so CRM seeds its quick filters."""
		frappe.db.delete("CRM Global Settings", {"dt": "Data Import"})
		add_default_quick_filters()

		filters = get_quick_filters("Data Import", cached=False)

		self.assertEqual([f["fieldname"] for f in filters], ["name", "reference_doctype", "status"])
		self.assertEqual(filters[0]["fieldtype"], "Data")
