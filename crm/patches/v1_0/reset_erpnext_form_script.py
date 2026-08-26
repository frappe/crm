import frappe

from crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings import get_crm_form_script


def execute():
	reset_erpnext_form_script()


def reset_erpnext_form_script():
	try:
		if frappe.db.exists("CRM Form Script", "Create Quotation from CRM Deal"):
			script = get_crm_form_script()
			frappe.db.set_value("CRM Form Script", "Create Quotation from CRM Deal", "script", script)
			return True
		return False
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error while resetting form script")
		return False
