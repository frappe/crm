import frappe
from frappe.model.document import Document

from crm.antek_materials.integrations.fastapi_sync import push_credit_status
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

	event_id = f"{doc.name}:{doc.modified}"
	payload = {
		"event": "credit_status_changed",
		"contract_id": contract.contract_id,
		"contractor_id": contract.contractor,
		"current_debt": float(contract.current_debt or 0),
		"credit_limit": float(contract.credit_limit or 0),
		"remaining_credit": float(contract.remaining_credit or 0),
		"credit_locked": bool(contract.credit_locked),
		"updated_at": frappe.utils.now_datetime().isoformat(),
	}
	try:
		push_credit_status(payload, event_id)
		contract.db_set("sync_status", "Synced", update_modified=False)
		contract.db_set("last_synced_at", frappe.utils.now_datetime(), update_modified=False)
		contract.db_set("last_sync_event_id", event_id, update_modified=False)
	except Exception as e:
		contract.db_set("sync_status", "Failed", update_modified=False)
		contract.db_set("sync_error", str(e), update_modified=False)

