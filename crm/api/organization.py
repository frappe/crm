import frappe
from frappe import _


@frappe.whitelist()
def get_linked_lead(organization: str):
    """Get a lead linked to an organization via custom_org field"""
    if not frappe.has_permission("CRM Organization", "read", organization):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    lead = frappe.get_all(
        "CRM Lead",
        filters={"custom_org": organization},
        fields=["name"],
        limit=1,
    )
    return lead[0].name if lead else None


@frappe.whitelist()
def create_lead_from_organization(organization: str):
    """Create a new CRM Lead from organization data"""
    if not frappe.has_permission("CRM Organization", "read", organization):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    if not frappe.has_permission("CRM Lead", "create"):
        frappe.throw(_("Not permitted to create Lead"), frappe.PermissionError)

    org_doc = frappe.get_cached_doc("CRM Organization", organization)

    lead = frappe.new_doc("CRM Lead")
    lead.first_name = org_doc.organization_name
    lead.organization = org_doc.organization_name
    lead.custom_org = org_doc.organization_name
    lead.website = org_doc.website
    lead.territory = org_doc.territory
    lead.industry = org_doc.industry
    lead.no_of_employees = org_doc.no_of_employees
    lead.annual_revenue = org_doc.annual_revenue
    lead.image = org_doc.organization_logo
    # Add contacts
    print(f"Finding contacts linked to organization {org_doc.organization_name}...")
    contacts = frappe.get_all(
        "Contact",
        or_filters=[
            ["custom_org", "=", org_doc.organization_name],
            ["company_name", "=", org_doc.organization_name],
        ],
        pluck="name",
    )
    print(f"Found {len(contacts)} contacts linked to organization {org_doc.organization_name}")
    for contact in contacts:
        lead.append("custom_contacts", {"contact": contact})
    lead.insert()

    return lead.name
