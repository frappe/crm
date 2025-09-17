import frappe
from frappe import _

@frappe.whitelist(allow_guest=False)
def get_funnel_data(doctype: str, value: str, filter_key: str = None):
    if not (doctype and value):
        frappe.throw(_("Missing required parameters"))

    # Define the correct field to use for stage based on doctype
    stage_field = "status" if doctype == "CRM Lead" else "custom_stage"

    # Define all stages to track
    stages = ["None", "Service Stage", "Pipeline Stage", "After Sales Stage"]

    # Get filtered documents
    if filter_key is None:
        docs = frappe.get_all(doctype, fields=[stage_field])
    else:
        filters = {filter_key: value}
        docs = frappe.get_all(doctype, filters=filters, fields=[stage_field])

    # Total number of matched documents
    total = len(docs)
    if total == 0:
        return {"message": {stage: 0 for stage in stages}}

    # Count stages
    stage_counts = {stage: 0 for stage in stages}
    for doc in docs:
        stage_value = doc.get(stage_field) or "None"
        if stage_value not in stages:
            stage_value = "None"
        stage_counts[stage_value] += 1

    # Convert counts to percentages
    stage_percentages = {
        stage: round((count / total) * 100, 2)
        for stage, count in stage_counts.items()
    }

    return {"message": stage_percentages}