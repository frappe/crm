"""Whitelisted API wrapper around ses_inbound_provision.provision().

Called from the SES Settings UI "Provision AWS Infrastructure" button.
Saves the returned ARNs back to CRM SES Settings so the user never
needs to copy-paste them manually.
"""
from __future__ import annotations

import frappe
from frappe import _

from crm.api.ses import _require_manager


@frappe.whitelist(methods=["POST"])
def provision(
    aws_region_inbound: str,
    recipient_domain: str,
    s3_bucket_name: str,
    sns_topic_name: str,
    webhook_url: str,
) -> dict:
    _require_manager()

    if not aws_region_inbound or not recipient_domain or not s3_bucket_name:
        frappe.throw(_("Inbound Region, Inbound Domain, and S3 Bucket Name are required."))

    from crm.email.ses_inbound_provision import provision as _provision

    result = _provision(
        aws_region_inbound=aws_region_inbound,
        recipient_domain=recipient_domain,
        s3_bucket_name=s3_bucket_name,
        sns_topic_name=sns_topic_name or "careverse-crm-inbound",
        webhook_url=webhook_url,
    )

    # Persist ARNs back to CRM SES Settings
    doc = frappe.get_doc("CRM SES Settings", "CRM SES Settings")
    doc.inbound_region = aws_region_inbound
    doc.inbound_domain = recipient_domain
    doc.s3_bucket_name = result["s3_bucket_name"]
    doc.sns_topic_arn = result["sns_topic_arn"]
    doc.save(ignore_permissions=True)  # SYSTEM-INTERNAL: manager check above
    frappe.clear_cache(doctype="CRM SES Settings")

    return result
