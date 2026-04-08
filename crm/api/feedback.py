# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def submit_feedback(subject, feedback_type, message, email=None):
	"""Submit user feedback from the CRM frontend by emailing crm@frappe.io."""
	if not subject:
		frappe.throw(_("Subject is required"), frappe.MandatoryError)
	if not feedback_type:
		frappe.throw(_("Feedback type is required"), frappe.MandatoryError)
	if not message:
		frappe.throw(_("Message is required"), frappe.MandatoryError)

	sender = frappe.session.user
	reply_to = email or sender

	body = f"""
<p><strong>Type:</strong> {feedback_type}</p>
<p><strong>From:</strong> {sender}</p>
<p><strong>Reply-To:</strong> {reply_to}</p>
<hr>
<p>{frappe.utils.escape_html(message)}</p>
"""

	frappe.sendmail(
		recipients=["crm@frappe.io"],
		subject=f"[CRM Feedback] {subject}",
		message=body,
		reply_to=reply_to,
		now=True,
	)

	return {"success": True}
