import frappe
from frappe.model.document import get_controller
from pypika import Criterion


@frappe.whitelist()
def sort_options(doctype: str):
	c = get_controller(doctype)

	if not hasattr(c, "sort_options"):
		return []

	return c.sort_options()

@frappe.whitelist()
def get_filterable_fields(doctype: str):
	DocField = frappe.qb.DocType("DocField")
	allowed_fieldtypes = [
		"Check",
		"Data",
		"Float",
		"Int",
		"Link",
		"Long Text",
		"Select",
		"Small Text",
		"Text Editor",
		"Text",
	]

	from_doc_fields = (
		frappe.qb.from_(DocField)
		.select(
			DocField.fieldname,
			DocField.fieldtype,
			DocField.label,
			DocField.name,
			DocField.options,
		)
		.where(DocField.parent == doctype)
		.where(DocField.hidden == False)
		.where(Criterion.any([DocField.fieldtype == i for i in allowed_fieldtypes]))
		.run(as_dict=True)
	)
	res = []
	res.extend(from_doc_fields)
	return res
