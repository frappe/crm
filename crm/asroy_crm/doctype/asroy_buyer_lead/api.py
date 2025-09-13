import frappe

from crm.api.doc import get_assigned_users, get_fields_meta
from crm.fcrm.doctype.crm_form_script.crm_form_script import get_form_script


@frappe.whitelist()
def get_lead(name):
	lead = frappe.get_doc("Asroy Buyer Lead", name).as_dict()

	lead["fields_meta"] = get_fields_meta("Asroy Buyer Lead")
	lead["_form_script"] = get_form_script("Asroy Buyer Lead")
	lead["_assign"] = get_assigned_users("Asroy Buyer Lead", lead.name)
	return lead