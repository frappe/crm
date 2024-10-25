import frappe
from frappe import _

from crm.api.doc import get_fields_meta, get_assigned_users
from crm.fcrm.doctype.crm_form_script.crm_form_script import get_form_script

@frappe.whitelist()
def get_deal(name):
	Deal = frappe.qb.DocType("CRM Deal")

	query = (
		frappe.qb.from_(Deal)
		.select("*")
		.where(Deal.name == name)
		.limit(1)
	)

	deal = query.run(as_dict=True)
	if not len(deal):
		frappe.throw(_("Deal not found"), frappe.DoesNotExistError)
	deal = deal.pop()

	# Get all child table doctypes linked to CRM Deal
	meta = frappe.get_meta("CRM Deal")
	child_tables = [df for df in meta.fields if df.fieldtype in ["Table","Table MultiSelect" ] ]

	deal['child_tables'] = {}

	for child_table in child_tables:
		child_doctype = child_table.options
		child_records = frappe.get_all(
			child_doctype,
			fields="*",
			filters={"parent": deal['name']}
		)
		deal['child_tables'][child_table.fieldname] = child_records

	deal["contacts"] = frappe.get_all(
		"CRM Contacts",
		filters={"parenttype": "CRM Deal", "parent": deal.name},
		fields=["contact", "is_primary"],
	)

	deal["doctype"] = "CRM Deal"
	deal["fields_meta"] = get_fields_meta("CRM Deal") 
	deal["_form_script"] = get_form_script('CRM Deal')
	deal["_assign"] = get_assigned_users("CRM Deal", deal.name, deal.owner)
	return deal

@frappe.whitelist()
def get_deal_contacts(name):
	contacts = frappe.get_all(
		"CRM Contacts",
		filters={"parenttype": "CRM Deal", "parent": name},
		fields=["contact", "is_primary"],
	)
	deal_contacts = []
	for contact in contacts:
		is_primary = contact.is_primary
		contact = frappe.get_doc("Contact", contact.contact).as_dict()
		def get_primary_email(contact):
			for email in contact.email_ids:
				if email.is_primary:
					return email.email_id
			return contact.email_ids[0].email_id if contact.email_ids else ""
		def get_primary_mobile_no(contact):
			for phone in contact.phone_nos:
				if phone.is_primary:
					return phone.phone
			return contact.phone_nos[0].phone if contact.phone_nos else ""
		_contact = {
			"name": contact.name,
			"image": contact.image,
			"full_name": contact.full_name,
			"email": get_primary_email(contact),
			"mobile_no": get_primary_mobile_no(contact),
			"is_primary": is_primary,
		}
		deal_contacts.append(_contact)
	return deal_contacts

@frappe.whitelist(methods=["POST", "PUT"])
def update_crm_deal_elements(name, deal_elements):
	# Fetch the CRM Deal by name
	deal = frappe.get_doc("CRM Deal", name)
	
	# Clear the existing deal elements
	deal.set("deal_elements", [])
	
	# Add new deal elements from the list of strings
	for element in deal_elements:
		deal.append("deal_elements", {
			"deal_elements": element,  # now element is the string itself
			"parent": name,
			"parentfield": "deal_elements",
			"parenttype": "CRM Deal",
			"doctype": "CRM Deal Elements"
		})
	
	# Save the updated CRM Deal document
	deal.save(ignore_permissions=True)
	frappe.db.commit()
 
	return {"name":name, "deal_elements":deal.deal_elements}


@frappe.whitelist(methods=["GET"])
def get_deal_elements():
	# Fetch all CRM Deal Elements
	deal_elements = frappe.get_all("CRM Deal Element", fields=["name"])
	return deal_elements