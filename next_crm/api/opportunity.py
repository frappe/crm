import frappe
from frappe import _

from next_crm.api.doc import get_assigned_users, get_fields_meta
from next_crm.ncrm.doctype.crm_form_script.crm_form_script import get_form_script


@frappe.whitelist()
def get_opportunity(name):
    Opportunity = frappe.qb.DocType("Opportunity")

    query = (
        frappe.qb.from_(Opportunity)
        .select("*")
        .where(Opportunity.name == name)
        .limit(1)
    )

    opportunity = query.run(as_dict=True)
    if not len(opportunity):
        frappe.throw(_("Opportunity not found"), frappe.DoesNotExistError)
    opportunity = opportunity.pop()

    opportunity["doctype"] = "Opportunity"
    opportunity["fields_meta"] = get_fields_meta("Opportunity")
    opportunity["_form_script"] = get_form_script("Opportunity")
    opportunity["_assign"] = get_assigned_users("Opportunity", opportunity.name)
    return opportunity


@frappe.whitelist()
def get_opportunity_addresses(name):

    opportunity = frappe.get_cached_doc("Opportunity", name)

    opportunity_addresses = frappe.get_list(
        "Address",
        fields=["address_line1", "phone", "title", "name"],
        filters=[
            [
                "Dynamic Link",
                "link_doctype",
                "in",
                ["Opportunity", opportunity.opportunity_from],
            ],
            ["Dynamic Link", "link_name", "in", [name, opportunity.party_name]],
        ],
        distinct=True,
    )
    return opportunity_addresses


@frappe.whitelist()
def add_address(opportunity, address):
    if not frappe.has_permission("Opportunity", "write", opportunity):
        frappe.throw(
            _("Not allowed to add address to Opportunity"), frappe.PermissionError
        )

    opportunity_doc = frappe.get_cached_doc("Opportunity", opportunity)
    address_doc = frappe.get_doc("Address", address)

    if opportunity_doc.opportunity_from:
        address_doc.append(
            "links",
            {
                "link_doctype": opportunity_doc.opportunity_from,
                "link_name": opportunity_doc.party_name,
            },
        )

    address_doc.append(
        "links", {"link_doctype": "Opportunity", "link_name": opportunity}
    )
    address_doc.save()
    return True


@frappe.whitelist()
def remove_address(opportunity, address):
    if not frappe.has_permission("Opportunity", "write", opportunity):
        frappe.throw(
            _("Not allowed to remove address from Opportunity"), frappe.PermissionError
        )

    opportunity_doc = frappe.get_cached_doc("Opportunity", opportunity)
    address_doc = frappe.get_doc("Address", address)
    link_names = [opportunity]
    if opportunity_doc.opportunity_from:
        link_names.append(opportunity_doc.party_name)
    address_doc.links = [d for d in address_doc.links if d.link_name not in link_names]
    address_doc.save()
    return True
