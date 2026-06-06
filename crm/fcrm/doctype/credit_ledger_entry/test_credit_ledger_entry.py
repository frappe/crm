import frappe
from frappe.tests import IntegrationTestCase


class IntegrationTestCreditLedgerEntry(IntegrationTestCase):
	def tearDown(self) -> None:
		frappe.db.rollback()

	def test_submit_recomputes_contract_debt(self):
		contract = frappe.get_doc(
			{
				"doctype": "Tripartite Contract",
				"contract_id": "HD-3B-2026-002",
				"credit_limit": 200000000,
			}
		).insert()
		entry = frappe.get_doc(
			{
				"doctype": "Credit Ledger Entry",
				"tripartite_contract": contract.name,
				"transaction_type": "Delivered",
				"amount": 10000000,
			}
		).insert()
		entry.submit()
		contract.reload()
		self.assertEqual(contract.current_debt, 10000000)
