# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMFormScript(Document):
	def validate(self):
		self.check_if_duplicate()

	def check_if_duplicate(self):
		"""Check if there is already a script for this doctype"""
		if self.dt and self.enabled:
			filters = {
				"dt": self.dt,
				"enabled": 1,
			}
			if self.name:
				filters["name"] = ["!=", self.name]

			if frappe.db.exists("CRM Form Script", filters):
				frappe.throw(
					frappe._(
						"Script already exists for this doctype and is enabled"
					),
					frappe.DuplicateEntryError,
				)

def get_form_script(dt):
	"""Returns the script for the given doctype"""
	FormScript = frappe.qb.DocType("CRM Form Script")
	query = (
		frappe.qb.from_(FormScript)
		.select("script")
		.where(FormScript.dt == dt)
		.where(FormScript.enabled == 1)
		.limit(1)
	)

	doc = query.run(as_dict=True)
	if doc:
		return doc[0].script
	else:
		return None
