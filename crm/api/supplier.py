import frappe
from frappe import _

@frappe.whitelist()
def get_supplier_sections(supplier):
	"""Get sections for supplier information"""
	doc = frappe.get_doc("Supplier", supplier)
	
	basic_info = {
		"title": "Basic Info",
		"fields": [
			{
				"label": "Supplier Name",
				"value": doc.supplier_name,
				"type": "Data"
			},
			{
				"label": "Supplier Group",
				"value": doc.supplier_group,
				"type": "Link"
			},
			{
				"label": "Supplier Type",
				"value": doc.supplier_type,
				"type": "Select"
			}
		]
	}
	
	contact_info = {
		"title": "Contact Info",
		"fields": [
			{
				"label": "Email",
				"value": doc.email_id,
				"type": "Data"
			},
			{
				"label": "Phone",
				"value": doc.phone,
				"type": "Data"
			},
			{
				"label": "Mobile",
				"value": doc.mobile_no,
				"type": "Data"
			},
			{
				"label": "Website",
				"value": doc.website,
				"type": "Data"
			}
		]
	}
	
	financial_info = {
		"title": "Financial Info",
		"fields": [
			{
				"label": "Tax ID",
				"value": doc.tax_id,
				"type": "Data"
			},
			{
				"label": "Default Currency",
				"value": doc.default_currency,
				"type": "Link"
			},
			{
				"label": "Payment Terms",
				"value": doc.payment_terms,
				"type": "Link"
			}
		]
	}
	
	return [basic_info, contact_info, financial_info]