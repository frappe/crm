import frappe


def execute():
	deal_statuses = frappe.get_all("CRM Deal Status", fields=["name", "type", "deal_status"])

	openStatuses = ["New", "Open", "Unassigned", "Qualification"]
	ongoingStatuses = [
		"Demo/Making",
		"Proposal/Quotation",
		"Negotiation",
		"Ready to Close",
		"Demo Scheduled",
		"Follow Up",
	]
	onHoldStatuses = ["On Hold", "Paused", "Stalled", "Awaiting Reply"]
	wonStatuses = ["Won", "Closed Won", "Successful", "Completed"]
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

	for status in deal_statuses:
		if not status.type or status.type is None or status.type == "Open":
			if status.deal_status in openStatuses:
				type = "Open"
			elif status.deal_status in ongoingStatuses:
				type = "Ongoing"
			elif status.deal_status in onHoldStatuses:
				type = "On Hold"
			elif status.deal_status in wonStatuses:
				type = "Won"
			elif status.deal_status in lostStatuses:
				type = "Lost"
			else:
				type = "Ongoing"

			frappe.db.set_value("CRM Deal Status", status.name, "type", type)
