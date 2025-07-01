import frappe


def execute():
	deal_statuses = frappe.get_all("CRM Deal Status", fields=["name", "probability", "deal_status"])

	for status in deal_statuses:
		if status.probability is None or status.probability == 0:
			if status.deal_status == "Qualification":
				probability = 10
			elif status.deal_status == "Demo/Making":
				probability = 25
			elif status.deal_status == "Proposal/Quotation":
				probability = 50
			elif status.deal_status == "Negotiation":
				probability = 70
			elif status.deal_status == "Ready to Close":
				probability = 90
			elif status.deal_status == "Won":
				probability = 100
			else:
				probability = 0

			frappe.db.set_value("CRM Deal Status", status.name, "probability", probability)
