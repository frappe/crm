# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.custom.doctype.property_setter.property_setter import delete_property_setter, make_property_setter
from frappe.model.document import Document

from crm.demo.api import create_demo_data
from crm.install import after_install


class FCRMSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.desk.doctype.event_notifications.event_notifications import EventNotifications
		from frappe.types import DF

		from crm.fcrm.doctype.crm_dropdown_item.crm_dropdown_item import CRMDropdownItem

		access_key: DF.Data | None
		all_day_event_notifications: DF.Table[EventNotifications]
		auto_mark_replied_on_response: DF.Check
		auto_reopen_on_new_communication: DF.Check
		auto_update_expected_deal_value: DF.Check
		brand_logo: DF.Attach | None
		brand_name: DF.Data | None
		currency: DF.Link | None
		default_calendar_view: DF.Literal["Daily", "Weekly", "Monthly"]
		dropdown_items: DF.Table[CRMDropdownItem]
		enable_forecasting: DF.Check
		event_notifications: DF.Table[EventNotifications]
		favicon: DF.Attach | None
		service_provider: DF.Literal[
			"frankfurter.app", "fawazahmed-exchange-api", "exchangerate.host", "exchangerate-api"
		]
		update_timestamp_on_new_communication: DF.Check
	# end: auto-generated types

	@frappe.whitelist()
	def restore_defaults(self, force: bool = False):
		after_install(force)

	@frappe.whitelist()
	def restore_demo_data(self):
		create_demo_data()

	def validate(self):
		self.do_not_allow_to_delete_if_standard()
		self.setup_forecasting()
		self.make_currency_read_only()

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
				self.remove_forecasting_section("Side Panel")
				self.remove_forecasting_section("Quick Entry")
				delete_property_setter(
					"CRM Deal",
					"reqd",
					"expected_closure_date",
				)
				delete_property_setter(
					"CRM Deal",
					"reqd",
					"expected_deal_value",
				)
			else:
				self.add_forecasting_section("Side Panel")
				self.add_forecasting_section("Quick Entry")
				make_property_setter(
					"CRM Deal",
					"expected_closure_date",
					"reqd",
					1 if self.enable_forecasting else 0,
					"Check",
				)
				make_property_setter(
					"CRM Deal",
					"expected_deal_value",
					"reqd",
					1 if self.enable_forecasting else 0,
					"Check",
				)

	def make_currency_read_only(self):
		if self.currency and self.has_value_changed("currency"):
			make_property_setter(
				"FCRM Settings",
				"currency",
				"read_only",
				1,
				"Check",
			)

	def add_forecasting_section(self, layout_type):
		layout_name = f"CRM Deal-{layout_type}"
		if not frappe.db.exists("CRM Fields Layout", layout_name):
			return
		doc = frappe.get_doc("CRM Fields Layout", layout_name)
		layout = json.loads(doc.layout) if doc.layout else []
		# layout is either a plain list of sections or a list of tabs with sections
		has_tabs = any("sections" in item for item in layout)
		sections = layout[-1].setdefault("sections", []) if has_tabs else layout
		all_sections = (
			[section for tab in layout for section in tab.get("sections", [])] if has_tabs else layout
		)
		if any(section.get("name") == "forecasted_sales_section" for section in all_sections):
			return
		# FIX: fields inside columns are dicts; extract "fieldname" string for set
		# comparison instead of using dicts as set elements (unhashable on Python 3.14)
		existing_fields = {
			(field.get("fieldname") or field.get("name")) if isinstance(field, dict) else field
			for section in all_sections
			for column in section.get("columns") or []
			for field in column.get("fields") or []
		}
		fields = [
			field
			for field in ("expected_deal_value", "expected_closure_date", "probability")
			if field not in existing_fields
		]
		if not fields:
			return

		if layout_type == "Side Panel":
			new_section = {
				"name": "forecasted_sales_section",
				"label": "Forecasted Sales",
				"opened": True,
				"columns": [{"name": "forecasted_sales_column", "fields": fields}],
			}
			# Insert after contacts_section if it's the first section, else insert at the beginning
			if sections and sections[0].get("name") == "contacts_section":
				sections.insert(1, new_section)
			else:
				sections.insert(0, new_section)
		else:
			# one column per field so they render in a single row
			new_section = {
				"name": "forecasted_sales_section",
				"columns": [{"name": field + "_column", "fields": [field]} for field in fields],
			}
			sections.append(new_section)

		doc.layout = json.dumps(layout)
		doc.save(ignore_permissions=True)

	def remove_forecasting_section(self, layout_type):
		layout_name = f"CRM Deal-{layout_type}"
		if not frappe.db.exists("CRM Fields Layout", layout_name):
			return
		doc = frappe.get_doc("CRM Fields Layout", layout_name)
		layout = json.loads(doc.layout) if doc.layout else []
		has_tabs = any("sections" in item for item in layout)
		if has_tabs:
			for tab in layout:
				tab["sections"] = [
					section
					for section in tab.get("sections", [])
					if section.get("name") != "forecasted_sales_section"
				]
		else:
			layout = [section for section in layout if section.get("name") != "forecasted_sales_section"]
		doc.layout = json.dumps(layout)
		doc.save(ignore_permissions=True)


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
