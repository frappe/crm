import frappe


def recompute_contract_balance(contract_name: str) -> tuple[float, float, int]:
	total_debt = (
		frappe.db.sql(
			"""
			select coalesce(sum(amount), 0)
			from `tabCredit Ledger Entry`
			where tripartite_contract = %s and docstatus = 1
			""",
			(contract_name,),
		)[0][0]
		or 0
	)
	contract = frappe.get_doc("Tripartite Contract", contract_name)
	remaining_credit = (contract.credit_limit or 0) - total_debt
	credit_locked = 1 if total_debt >= (contract.credit_limit or 0) else 0
	return float(total_debt), float(remaining_credit), credit_locked
