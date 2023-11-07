import json

import frappe
from frappe import _
from frappe.desk.form.load import get_docinfo
from crm.fcrm.doctype.crm_lead.api import get_activities as get_lead_activities


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
