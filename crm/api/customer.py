import frappe
from frappe import _

@frappe.whitelist()
def get_customer_sections(customer):
	"""Get sections for customer information"""
	doc = frappe.get_doc("Customer", customer)
	
	basic_info = {
		"title": "Basic Info",
		"fields": [
			{
				"label": "Customer Name",
				"value": doc.customer_name,
				"type": "Data"
			},
			{
				"label": "Customer Group",
				"value": doc.customer_group,
				"type": "Link"
			},
			{
				"label": "Customer Type",
				"value": doc.customer_type,
				"type": "Select"
			},
			{
				"label": "Territory",
				"value": doc.territory,
				"type": "Link"
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
				"label": "Credit Limit",
				"value": doc.credit_limit,
				"type": "Currency"
			},
			{
				"label": "Payment Terms",
				"value": doc.payment_terms,
				"type": "Link"
			}
		]
	}
	
	return [basic_info, contact_info, financial_info]