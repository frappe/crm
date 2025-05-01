import frappe
from pypika import Criterion


@frappe.whitelist()
def get_scripts(doctype, view="Form"):
	Script = frappe.qb.DocType("CRM Form Script")
	query = (
		frappe.qb.from_(Script)
		.select("*")
		.where(Script.dt == doctype)
		.where(Script.view == view)
		.where(Script.enabled == 1)
	)

	scripts = query.run(as_dict=True)
	return scripts
