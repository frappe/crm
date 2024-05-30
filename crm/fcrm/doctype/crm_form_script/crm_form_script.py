# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMFormScript(Document):
	pass

def get_form_script(dt, view="Form"):
	"""Returns the form script for the given doctype"""
	FormScript = frappe.qb.DocType("CRM Form Script")
	query = (
		frappe.qb.from_(FormScript)
		.select("script")
		.where(FormScript.dt == dt)
		.where(FormScript.view == view)
		.where(FormScript.enabled == 1)
	)

	doc = query.run(as_dict=True)
	if doc:
		return [d.script for d in doc] if len(doc) > 1 else doc[0].script
	else:
		return None
