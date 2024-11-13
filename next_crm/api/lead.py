import frappe
from frappe import _

from next_crm.api.doc import get_fields_meta, get_assigned_users
from next_crm.ncrm.doctype.crm_form_script.crm_form_script import get_form_script

@frappe.whitelist()
def get_lead(name):
	Lead = frappe.qb.DocType("Lead")

	query = frappe.qb.from_(Lead).select("*").where(Lead.name == name).limit(1)

	lead = query.run(as_dict=True)
	if not len(lead):
		frappe.throw(_("Lead not found"), frappe.DoesNotExistError)
	lead = lead.pop()

	lead["doctype"] = "Lead"
	lead["fields_meta"] = get_fields_meta("Lead")
	lead["_form_script"] = get_form_script('Lead')
	lead["_assign"] = get_assigned_users("Lead", lead.name, lead.owner)
	return lead