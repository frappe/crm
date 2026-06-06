import frappe
from frappe.model.document import Document

from crm.antek_materials.services.credit_contract_service import recompute_contract_balance


class CreditLedgerEntry(Document):
	def on_submit(self):
		handle_credit_ledger_submit(self)


def handle_credit_ledger_submit(doc, method=None):
	total_debt, remaining_credit, credit_locked = recompute_contract_balance(doc.tripartite_contract)
	contract = frappe.get_doc("Tripartite Contract", doc.tripartite_contract)
	contract.current_debt = total_debt
	contract.remaining_credit = remaining_credit
	contract.credit_locked = credit_locked
	contract.sync_status = "Pending"
	contract.sync_error = None
	contract.save(ignore_permissions=True)
