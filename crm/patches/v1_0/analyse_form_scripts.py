import frappe

from crm.fcrm.doctype.crm_form_script.crm_form_script import refresh_analysis


def execute():
	for name in frappe.get_all("CRM Form Script", pluck="name"):
		refresh_analysis(name)
