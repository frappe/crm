import frappe
from frappe import _

from next_crm.api.doc import get_assigned_users, get_fields_meta
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
    lead["_form_script"] = get_form_script("Lead")
    lead["_assign"] = get_assigned_users("Lead", lead.name)
    return lead


@frappe.whitelist()
def get_lead_addresses(name):
    lead_addresses = frappe.get_list(
        "Address",
        fields=["address_line1", "phone", "title", "name"],
        filters=[
            ["Dynamic Link", "link_doctype", "=", "Lead"],
            ["Dynamic Link", "link_name", "=", name],
        ],
        distinct=True,
    )
    return lead_addresses


@frappe.whitelist()
def remove_address(lead, address):
    if not frappe.has_permission("Lead", "write", lead):
        frappe.throw(
            _("Not allowed to remove address from Lead"), frappe.PermissionError
        )

    address_doc = frappe.get_doc("Address", address)
    address_doc.links = [d for d in address_doc.links if d.link_name != lead]
    address_doc.save()
    return True
