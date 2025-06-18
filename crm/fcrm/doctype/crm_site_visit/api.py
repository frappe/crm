import frappe

from crm.api.doc import get_assigned_users, get_fields_meta
from crm.fcrm.doctype.crm_form_script.crm_form_script import get_form_script

@frappe.whitelist()
def get_visit(name):
	visit = frappe.get_doc("CRM Site Visit", name)
	visit.check_permission("read")

	visit = visit.as_dict()

	visit["fields_meta"] = get_fields_meta("CRM Site Visit")
	visit["_form_script"] = get_form_script("CRM Site Visit")
	visit["_assign"] = get_assigned_users("CRM Site Visit", visit.name)
	return visit