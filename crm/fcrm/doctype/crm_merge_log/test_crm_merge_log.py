import frappe
from frappe.tests import IntegrationTestCase


class TestCRMMergeLog(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def _create_lead(self, **kwargs):
		data = {"doctype": "CRM Lead"}
		data.update(kwargs)
		return frappe.get_doc(data).insert(ignore_permissions=True)

	def test_merge_log_creation(self):
		lead_a = self._create_lead(first_name="A", email="a_log@test.com")
		lead_b = self._create_lead(first_name="B", email="b_log@test.com")

		log = frappe.get_doc(
			{
				"doctype": "CRM Merge Log",
				"reference_doctype": "CRM Lead",
				"target_document_name": lead_a.name,
				"source_document_name": lead_b.name,
			}
		)
		log.insert(ignore_permissions=True)

		self.assertTrue(log.merged_at)
		self.assertTrue(log.merged_by)
		self.assertEqual(log.reference_doctype, "CRM Lead")
		self.assertEqual(log.target_document_name, lead_a.name)
		self.assertEqual(log.source_document_name, lead_b.name)

	def test_merge_log_rejects_same_target_source(self):
		lead = self._create_lead(first_name="Same", email="same_log@test.com")

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "CRM Merge Log",
					"reference_doctype": "CRM Lead",
					"target_document_name": lead.name,
					"source_document_name": lead.name,
				}
			).insert(ignore_permissions=True)
