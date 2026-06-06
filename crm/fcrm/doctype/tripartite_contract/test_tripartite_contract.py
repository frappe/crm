import frappe
from frappe.tests import IntegrationTestCase


class IntegrationTestTripartiteContract(IntegrationTestCase):
	def tearDown(self) -> None:
		frappe.db.rollback()

	def test_remaining_credit_and_lock_flag(self):
		doc = frappe.get_doc(
			{
				"doctype": "Tripartite Contract",
				"contract_id": "HD-3B-2026-001",
				"credit_limit": 200000000,
				"current_debt": 200000000,
			}
		).insert()
		doc.reload()
		self.assertEqual(doc.remaining_credit, 0)
		self.assertEqual(doc.credit_locked, 1)
