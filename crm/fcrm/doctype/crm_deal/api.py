import frappe
from frappe import _


@frappe.whitelist()
def get_deal(name):
	Deal = frappe.qb.DocType("CRM Deal")

	query = (
		frappe.qb.from_(Deal)
		.select("*")
		.where(Deal.name == name)
		.limit(1)
	)

	deal = query.run(as_dict=True)
	if not len(deal):
		frappe.throw(_("Deal not found"), frappe.DoesNotExistError)
	deal = deal.pop()

	return deal
