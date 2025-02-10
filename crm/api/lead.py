import frappe


@frappe.whitelist()
def delete_lead_and_links(name):
	linked_doctypes = {
		'Communication': 'reference_name',
		'Comment': 'reference_name',
		'CRM Call Log': 'reference_docname',
		'CRM Task': 'reference_docname',
		'FCRM Note': 'reference_docname',
		'File': 'attached_to_name'
	}
	for doctype, fieldname in linked_doctypes.items():
		linked_docs = frappe.get_all(doctype, filters={fieldname: name})
		for doc in linked_docs:
			frappe.delete_doc(doctype, doc.name)

	frappe.delete_doc('CRM Lead', name)
