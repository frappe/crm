import frappe


@frappe.whitelist()
def delete_lead_and_links(name):
	print(name)
	linked_doctypes = {
		'Communication': 'reference_name',
		'Comment': 'reference_name',
		'File': 'attached_to_name',
		'Dynamic Link': 'link_name',
		'CRM Call Log': 'reference_docname',
		'CRM Task': 'reference_docname',
		'CRM Notification': 'reference_name',
		'FCRM Note': 'reference_docname',
	}
	for doctype, fieldname in linked_doctypes.items():
		print(doctype)
		print(fieldname)
		linked_docs = frappe.get_all(doctype, filters={fieldname: name})
		print(linked_docs)
		for doc in linked_docs:
			frappe.delete_doc(doctype, doc.name)

	frappe.delete_doc('CRM Lead', name)
