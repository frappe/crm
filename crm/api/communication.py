import frappe

def update_lead_communication_status(doc, method=None):
	"""
	Update CRM Lead communication status based on the latest communication.
	If the latest communication is 'Received', status is 'Replied'.
	If the latest communication is 'Sent', status is 'Open'.
	"""
	if doc.reference_doctype != "CRM Lead":
		return

	if doc.sent_or_received not in ("Sent", "Received"):
		return

	# Determine the new status based on the current communication
	status = "Replied" if doc.sent_or_received == "Received" else "Open"

	# Check if this is the latest communication for the lead
	latest_communication = frappe.db.get_value(
		"Communication",
		{
			"reference_doctype": "CRM Lead",
			"reference_name": doc.reference_name,
			"sent_or_received": ["in", ["Sent", "Received"]]
		},
		"name",
		order_by="creation desc"
	)

	# Only update if the current communication is the latest one
	if latest_communication == doc.name:
		frappe.db.set_value("CRM Lead", doc.reference_name, "communication_status", status)
