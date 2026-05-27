# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from crm.fcrm.doctype.crm_product.sync_utils import payload_differs, same_site_sync_active

CATALOGUE_FIELDS = ("standard_rate", "image", "disabled", "description")


class CRMProduct(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		description: DF.TextEditor | None
		disabled: DF.Check
		image: DF.AttachImage | None
		naming_series: DF.Literal["CRM-PROD-.YYYY.-"]
		product_code: DF.Data
		product_name: DF.Data | None
		standard_rate: DF.Currency
	# end: auto-generated types

	def validate(self):
		self.set_product_name()

	def set_product_name(self):
		self.product_name = (self.product_name or self.product_code or "").strip()

	def after_insert(self):
		if self.flags.get("ignore_erpnext_sync"):
			return
		if not same_site_sync_active():
			return
		if self.get("erpnext_item_code"):
			return
		_create_item_from_product(self)

	def on_update(self):
		if self.flags.get("ignore_erpnext_sync"):
			return
		if not self.get("erpnext_item_code"):
			return
		if not same_site_sync_active():
			return
		_push_to_item(self)

	def on_trash(self):
		if not self.get("erpnext_item_code"):
			return
		if not same_site_sync_active():
			return
		if frappe.db.sql(
			"SELECT 1 FROM `tabQuotation Item` WHERE item_code=%s LIMIT 1",
			self.erpnext_item_code,
		):
			frappe.throw(
				_(
					"Cannot delete: linked ERPNext Item {0} is referenced by a Quotation. "
					"Remove the reference or delete the Item in ERPNext first."
				).format(self.erpnext_item_code)
			)


def _create_item_from_product(doc):
	if frappe.db.exists("Item", doc.product_code):
		return
	item = frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": doc.product_code,
			"item_name": doc.product_name or doc.product_code,
			"standard_rate": doc.standard_rate,
			"image": doc.image,
			"disabled": doc.disabled,
			"description": doc.description,
			"crm_product_code": doc.name,
			"item_group": frappe.db.get_single_value("Stock Settings", "item_group") or "All Item Groups",
			"stock_uom": frappe.db.get_single_value("Stock Settings", "stock_uom") or "Nos",
			"is_stock_item": 0,
		}
	)
	item.flags.ignore_crm_sync = True
	item.insert()
	frappe.db.set_value("CRM Product", doc.name, "erpnext_item_code", item.name)


def _push_to_item(doc):
	item_code = doc.erpnext_item_code
	if not frappe.db.exists("Item", item_code):
		frappe.db.set_value("CRM Product", doc.name, "erpnext_item_code", None)
		return
	data = {"item_name": doc.product_name, **{f: doc.get(f) for f in CATALOGUE_FIELDS}}
	current = frappe.db.get_value("Item", item_code, list(data.keys()), as_dict=True) or {}
	if not payload_differs(data, current):
		return
	item = frappe.get_doc("Item", item_code)
	item.update(data)
	item.flags.ignore_crm_sync = True
	item.save()
