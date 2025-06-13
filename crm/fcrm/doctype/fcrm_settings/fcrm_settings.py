# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.custom.doctype.property_setter.property_setter import delete_property_setter, make_property_setter
from frappe.model.document import Document

from crm.install import after_install


class FCRMSettings(Document):
	@frappe.whitelist()
	def restore_defaults(self, force=False):
		after_install(force)

	def validate(self):
		self.do_not_allow_to_delete_if_standard()
		self.setup_forecasting()

	def do_not_allow_to_delete_if_standard(self):
		if not self.has_value_changed("dropdown_items"):
			return
		old_items = self.get_doc_before_save().get("dropdown_items")
		standard_new_items = [d.name1 for d in self.dropdown_items if d.is_standard]
		standard_old_items = [d.name1 for d in old_items if d.is_standard]
		deleted_standard_items = set(standard_old_items) - set(standard_new_items)
		if deleted_standard_items:
			standard_dropdown_items = get_standard_dropdown_items()
			if not deleted_standard_items.intersection(standard_dropdown_items):
				return
			frappe.throw(_("Cannot delete standard items {0}").format(", ".join(deleted_standard_items)))

	def setup_forecasting(self):
		if self.has_value_changed("enable_forecasting"):
			if not self.enable_forecasting:
				delete_property_setter(
					"CRM Deal",
					"reqd",
					"close_date",
				)
			else:
				make_property_setter(
					"CRM Deal",
					"close_date",
					"reqd",
					1 if self.enable_forecasting else 0,
					"Check",
				)


def get_standard_dropdown_items():
	return [item.get("name1") for item in frappe.get_hooks("standard_dropdown_items")]


def after_migrate():
	sync_table("dropdown_items", "standard_dropdown_items")


def sync_table(key, hook):
	crm_settings = FCRMSettings("FCRM Settings")
	existing_items = {d.name1: d for d in crm_settings.get(key)}
	new_standard_items = {}

	# add new items
	count = 0  # maintain count because list may come from seperate apps
	for item in frappe.get_hooks(hook):
		if item.get("name1") not in existing_items:
			crm_settings.append(key, item, count)
		new_standard_items[item.get("name1")] = True
		count += 1

	# remove unused items
	items = crm_settings.get(key)
	items = [item for item in items if not (item.is_standard and (item.name1 not in new_standard_items))]
	crm_settings.set(key, items)

	crm_settings.save()


def create_forecasting_script():
	if not frappe.db.exists("CRM Form Script", "Forecasting Script"):
		script = get_forecasting_script()
		frappe.get_doc(
			{
				"doctype": "CRM Form Script",
				"name": "Forecasting Script",
				"dt": "CRM Deal",
				"view": "Form",
				"script": script,
				"enabled": 1,
				"is_standard": 1,
			}
		).insert()


def get_forecasting_script():
	return """class CRMDeal {
    async status() {
        await this.doc.trigger('updateProbability')
    }
    async updateProbability() {
        let status = await call("frappe.client.get_value", {
            doctype: "CRM Deal Status",
            fieldname: "probability",
            filters: { name: this.doc.status },
        })

        this.doc.probability = status.probability
    }
}"""
