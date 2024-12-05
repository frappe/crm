import frappe
from frappe import _

from crm.api.doc import get_fields_meta, get_assigned_users
from crm.fcrm.doctype.crm_form_script.crm_form_script import get_form_script

@frappe.whitelist()
def get_lead(name):
	Lead = frappe.qb.DocType("CRM Lead")

	query = frappe.qb.from_(Lead).select("*").where(Lead.name == name).limit(1)

	lead = query.run(as_dict=True)
	if not len(lead):
		frappe.throw(_("Lead not found"), frappe.DoesNotExistError)
	lead = lead.pop()

	lead["doctype"] = "CRM Lead"
	lead["fields_meta"] = get_fields_meta("CRM Lead")
	lead["_form_script"] = get_form_script('CRM Lead')
	lead["_assign"] = get_assigned_users("CRM Lead", lead.name, lead.owner)
	organization_name = frappe.db.get_value("CRM Lead", lead.name, "organization") 
	if organization_name:
		lead['partner_leads'] = frappe.get_list("CRM Lead", filters=[["organization",'=',organization_name],['status','!=','Contacted'],['converted','!=',1]], fields=["name"])
	else:
		lead['partner_leads'] = []
	return lead
