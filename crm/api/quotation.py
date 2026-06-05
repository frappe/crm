import frappe
from frappe import _


@frappe.whitelist()
def get_available_inquiries(search=None):
    """Existing function - keep this"""
    used_inquiries = frappe.get_all(
        "CRM Quotation",
        fields=["inquiry"],
        filters={"inquiry": ["is", "set"]},
        pluck="inquiry",
    )
    filters = {"status": "Won"}
    if used_inquiries:
        filters["name"] = ["not in", used_inquiries]
    if search:
        filters["organization"] = ["like", f"%{search}%"]
    return frappe.get_all(
        "CRM Deal",
        fields=["name", "organization", "deal_owner"],
        filters=filters,
        order_by="modified desc",
        limit=50,
    )


@frappe.whitelist()
def get_inquiry_detail(name):
    """Detail CRM Deal (inquiry) untuk ditampilkan di sidebar Quotation."""
    if not name or not frappe.db.exists("CRM Deal", name):
        return {}

    deal = frappe.get_doc("CRM Deal", name)

    # Contact utama: field `contact`, atau baris is_primary di child table `contacts`.
    contact = deal.contact
    if not contact and deal.contacts:
        primary = next((c for c in deal.contacts if c.is_primary), deal.contacts[0])
        contact = primary.contact

    # Ambil full_name terkini dari dokumen Contact (child table bisa stale).
    contact_name = None
    if contact:
        contact_name = frappe.db.get_value("Contact", contact, "full_name") or contact

    return {
        "name": deal.name,
        "organization": deal.organization,
        "subject": getattr(deal, "subject", None),
        "status": deal.status,
        "deal_owner": deal.deal_owner,
        "contact": contact,
        "contact_name": contact_name,
        "email": deal.email,
        "mobile_no": deal.mobile_no,
        "territory": deal.territory,
        "source": deal.source,
        "currency": deal.currency,
        "deal_value": deal.deal_value,
    }


@frappe.whitelist()
def get_quotation_contacts(name):
    """Get contacts linked to quotation's account (organization)"""
    quotation = frappe.get_doc("CRM Quotation", name)
    if not quotation.account:
        return []
    
    contacts = frappe.get_all(
        "Contact",
        filters={"company_name": quotation.account},
        fields=["name", "first_name", "last_name", "image"],
    )
    
    result = []
    for c in contacts:
        contact_doc = frappe.get_doc("Contact", c.name)
        primary_email = next(
            (e.email_id for e in contact_doc.email_ids if e.is_primary), None
        )
        primary_phone = next(
            (p.phone for p in contact_doc.phone_nos if p.is_primary_mobile_no),
            None,
        )
        full_name = f"{c.first_name or ''} {c.last_name or ''}".strip()
        result.append({
            "name": c.name,
            "full_name": full_name or c.name,
            "image": c.image,
            "email": primary_email,
            "mobile_no": primary_phone,
        })
    return result