import frappe
from crm.fcrm.doctype.crm_lead.crm_lead import convert_to_deal

@frappe.whitelist()
def update_lead_stage(doc, method=None):
    if isinstance(doc, dict):
        doc = frappe.get_doc(doc)

    if doc.reference_doctype == "CRM Lead" and doc.reference_docname:
        lead = frappe.get_doc("CRM Lead", doc.reference_docname)

        # new_stage = None

        when_status_none = {
            "Call": "Service Stage",
            "Meeting": "Service Stage",
            "Property Visit": "Service Stage",
            "Viewing": "Service Stage",
            "Close": "Service Stage",
            "Price Offer Received": "Pipeline Stage",
            "Booking": "After Sales Stage",
        }

        when_status_service = {
            "Price Offer Received": "Pipeline Stage",
            "Negotiation": "Pipeline Stage",
            "Confirm": "Pipeline Stage",
            "Close": "Pipeline Stage",
            "Booking": "After Sales Stage",
        }

        when_status_pipeline = {
            "Price Offer Received": "Pipeline Stage",
            "Booking": "After Sales Stage",
            "Deed Signing": "After Sales Stage",
            "Sale Permission": "After Sales Stage",
            "Registration": "After Sales Stage",
            "Success": "After Sales Stage",
        }

        when_status_after_sales = {
            "Booking": "After Sales Stage",
            "Deed Signing": "After Sales Stage",
            "Sale Permission": "After Sales Stage",
            "Registration": "After Sales Stage",
            "Success": "After Sales Stage",
        }

        new_stage = None
        deal = None

        if lead.status == "None":
            new_stage = when_status_none.get(doc.custom_type)
            # deal = convert_to_deal(lead=lead)

        elif lead.status == "Service Stage":
            new_stage = when_status_service.get(doc.custom_type)

        elif lead.status == "Pipeline Stage":
            new_stage = when_status_pipeline.get(doc.custom_type)

        elif lead.status == "After Sales Stage":
            new_stage = when_status_after_sales.get(doc.custom_type)

        if new_stage and lead.status != new_stage:
            lead.reload()
            lead.status = new_stage
            lead.save(ignore_permissions=True)

        return lead if lead else None
    

@frappe.whitelist()
def update_deal_stage(doc, method=None):
    if isinstance(doc, dict):
        doc = frappe.get_doc(doc)

    if doc.reference_doctype == "CRM Deal" and doc.reference_docname:
        deal = frappe.get_doc("CRM Deal", doc.reference_docname)

        stage_transitions = {
            "Service Stage": {
                "Price Offer Received": "Pipeline Stage",
                "Negotiation": "Pipeline Stage",
                "Confirm": "Pipeline Stage",
                "Close": "Pipeline Stage",
                "Booking": "After Sales Stage",
            },
            "Pipeline Stage": {
                "Price Offer Received": "Pipeline Stage",
                "Booking": "After Sales Stage",
                "Deed Signing": "After Sales Stage",
                "Sale Permission": "After Sales Stage",
                "Registration": "After Sales Stage",
                "Success": "After Sales Stage",
            },
            "After Sales Stage": {
                "Booking": "After Sales Stage",
                "Deed Signing": "After Sales Stage",
                "Sale Permission": "After Sales Stage",
                "Registration": "After Sales Stage",
                "Success": "After Sales Stage",
            },
        }

        new_stage = stage_transitions.get(deal.status, {}).get(doc.custom_type)

        if new_stage and deal.status != new_stage:
            deal.reload()
            deal.status = new_stage
            deal.save(ignore_permissions=True)

        return deal if new_stage else None

