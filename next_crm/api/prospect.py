import frappe
from frappe import _

from next_crm.api.doc import get_assigned_users, get_fields_meta
from next_crm.ncrm.doctype.crm_form_script.crm_form_script import get_form_script


@frappe.whitelist()
def get_prospect(name):
    Prospect = frappe.qb.DocType("Prospect")

    query = frappe.qb.from_(Prospect).select("*").where(Prospect.name == name).limit(1)

    prospect = query.run(as_dict=True)
    if not len(prospect):
        frappe.throw(_("Prospect not found"), frappe.DoesNotExistError)
    prospect = prospect.pop()

    prospect["doctype"] = "Prospect"
    prospect["fields_meta"] = get_fields_meta("Prospect")
    prospect["_form_script"] = get_form_script("Prospect")
    prospect["_assign"] = get_assigned_users("Prospect", prospect.name, prospect.owner)
    return prospect
