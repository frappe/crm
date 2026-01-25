import frappe

def update_lead_communication_status(doc, method=None):
	if doc.reference_doctype != "CRM Lead":
		return

	if doc.sent_or_received not in ("Sent", "Received"):
		return

	# Status Logic
	status = "Replied" if doc.sent_or_received == "Received" else "Open"

	# Check if this is the latest communication to avoid overwriting newer data
	if doc.sent_or_received == "Sent":
		if frappe.db.exists("Communication", {
			"reference_doctype": doc.reference_doctype,
			"reference_name": doc.reference_name,
			"creation": (">", doc.creation),
			"name": ("!=", doc.name)
		}):
			return

	# Update Lead Doc
	lead_doc = frappe.get_doc("CRM Lead", doc.reference_name)
	if lead_doc.status != status:
		lead_doc.status = status
		lead_doc.save(ignore_permissions=True)
