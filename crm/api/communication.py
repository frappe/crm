import frappe
from frappe import _


def before_insert(doc, method):
	if doc.sent_or_received != "Received" or doc.communication_medium != "Email":
		return

	if doc.reference_doctype is not None or doc.reference_name is not None:
		return

	lead = frappe.get_all("CRM Lead", filters={"email": doc.sender}, fields=["name"])
	if not lead:
		return

	doc.reference_doctype = "CRM Lead"
	doc.reference_name = lead[0].name


