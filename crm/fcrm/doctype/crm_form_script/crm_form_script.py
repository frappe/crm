# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMFormScript(Document):
	def validate(self):
		in_user_env = not (
			frappe.flags.in_install
			or frappe.flags.in_patch
			or frappe.flags.in_test
			or frappe.flags.in_fixtures
		)
		if in_user_env and not self.is_new() and self.is_standard and not frappe.conf.developer_mode:
			# only enabled can be changed for standard form scripts
			if self.has_value_changed("enabled"):
				enabled_value = self.enabled
				self.reload()
				self.enabled = enabled_value
			else:
				frappe.throw(_("You need to be in developer mode to edit a Standard Form Script"))

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
