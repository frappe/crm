import frappe
from frappe.tests import IntegrationTestCase


class TestCRMMergeLog(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_merge_log_creation(self):
		log = frappe.get_doc(
			{
				"doctype": "CRM Merge Log",
				"reference_doctype": "CRM Lead",
				"target_document_name": "LEAD-0001",
				"source_document_name": "LEAD-0002",
			}
		)
		log.insert(ignore_permissions=True)

		self.assertTrue(log.merged_at)
		self.assertTrue(log.merged_by)
		self.assertEqual(log.reference_doctype, "CRM Lead")
		self.assertEqual(log.target_document_name, "LEAD-0001")
		self.assertEqual(log.source_document_name, "LEAD-0002")

	def test_merge_log_rejects_same_target_source(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "CRM Merge Log",
					"reference_doctype": "CRM Lead",
					"target_document_name": "LEAD-0001",
					"source_document_name": "LEAD-0001",
				}
			).insert(ignore_permissions=True)
