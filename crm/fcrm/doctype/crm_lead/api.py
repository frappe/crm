import frappe
from frappe import _

from crm.api.doc import get_doctype_fields

@frappe.whitelist()
def get_lead(name):
	Lead = frappe.qb.DocType("CRM Lead")

	query = frappe.qb.from_(Lead).select("*").where(Lead.name == name).limit(1)

	lead = query.run(as_dict=True)
	if not len(lead):
		frappe.throw(_("Lead not found"), frappe.DoesNotExistError)
	lead = lead.pop()

	lead["doctype_fields"] = get_doctype_fields("CRM Lead")
	return lead