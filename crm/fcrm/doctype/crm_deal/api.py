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


	deal["contacts"] = frappe.get_all(
		"CRM Contacts",
		filters={"parenttype": "CRM Deal", "parent": deal.name},
		fields=["contact", "is_primary"],
	)

	return deal
