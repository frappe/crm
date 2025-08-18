# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HelpdeskCRMSettings(Document):
	def validate(self):
		if self.enabled:
			self.validate_if_helpdesk_installed()
			self.create_helpdesk_script()

	def validate_if_helpdesk_installed(self):
		if not self.is_helpdesk_in_different_site:
			if "helpdesk" not in frappe.get_installed_apps():
				frappe.throw(_("Helpdesk is not installed in the current site"))

	def create_helpdesk_script(self):
		if not frappe.db.exists("CRM Form Script", "Helpdesk Integration Script"):
			script = get_helpdesk_script()
			frappe.get_doc(
				{
					"doctype": "CRM Form Script",
					"name": "Helpdesk Integration Script",
					"dt": "CRM Deal",
					"view": "Form",
					"script": script,
					"enabled": 1,
					"is_standard": 1,
				}
			).insert()


def get_helpdesk_script():
	return """class CRMDeal {
    onLoad() {
        this.actions.push(
            {
                group: "Helpdesk",
                hideLabel: true,
                items: [
                    {
                        label: "Create customer in Helpdesk",
                        onClick: () => {
                            toast.success("Success Message")
                        }
                    }
                ]
            }
        )
    }
}"""
