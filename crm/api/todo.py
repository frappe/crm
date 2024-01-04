import frappe

def after_insert(doc, method):
	if doc.reference_type in ["CRM Lead", "CRM Deal"] and doc.reference_name and doc.allocated_to:
		fieldname = "lead_owner" if doc.reference_type == "CRM Lead" else "deal_owner"
		lead_owner = frappe.db.get_value(doc.reference_type, doc.reference_name, fieldname)
		if not lead_owner:
			frappe.db.set_value(doc.reference_type, doc.reference_name, fieldname, doc.allocated_to)