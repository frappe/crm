import frappe


def execute():
	if not frappe.db.exists("CRM Lead Status", "Converted"):
		status_doc = frappe.get_doc(
			{
				"doctype": "CRM Lead Status",
				"lead_status": "Converted",
				"color": "teal",
				"type": "Won",
				"position": 5,
			}
		)
		status_doc.insert()

	lead_statuses = frappe.get_all("CRM Lead Status", fields=["name", "type", "lead_status"])

	openStatuses = ["New", "Open", "Unassigned"]
	ongoingStatuses = [
		"Contacted",
		"Nurture",
		"Interested",
		"Demo/Making",
		"Proposal/Quotation",
		"Negotiation",
		"Ready to Close",
		"Demo Scheduled",
		"Follow Up",
	]
	onHoldStatuses = ["On Hold", "Paused", "Stalled", "Awaiting Reply"]
	wonStatuses = ["Won", "Closed Won", "Successful", "Completed", "Qualified", "Converted"]
	lostStatuses = [
		"Lost",
		"Closed",
		"Closed Lost",
		"Junk",
		"Unqualified",
		"Disqualified",
		"Cancelled",
		"No Response",
	]

	for status in lead_statuses:
		if not status.type or status.type is None or status.type == "Open":
			if status.lead_status in openStatuses:
				type = "Open"
			elif status.lead_status in ongoingStatuses:
				type = "Ongoing"
			elif status.lead_status in onHoldStatuses:
				type = "On Hold"
			elif status.lead_status in wonStatuses:
				type = "Won"
			elif status.lead_status in lostStatuses:
				type = "Lost"
			else:
				type = "Ongoing"

			frappe.db.set_value("CRM Lead Status", status.name, "type", type)
