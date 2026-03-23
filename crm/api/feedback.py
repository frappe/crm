# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def submit_feedback(subject, feedback_type, message, email=None):
	"""Submit user feedback from the CRM frontend."""
	if not subject:
		frappe.throw(_("Subject is required"), frappe.MandatoryError)
	if not feedback_type:
		frappe.throw(_("Feedback type is required"), frappe.MandatoryError)
	if not message:
		frappe.throw(_("Message is required"), frappe.MandatoryError)

	doc = frappe.new_doc("CRM Feedback")
	doc.subject = subject
	doc.feedback_type = feedback_type
	doc.message = message
	doc.email = email or ""
	doc.insert(ignore_permissions=True)

	return {"success": True, "name": doc.name}
