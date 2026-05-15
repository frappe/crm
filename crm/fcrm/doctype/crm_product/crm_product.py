# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


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

	def before_insert(self):
		if self.flags.get("ignore_erpnext_sync"):
			return
		if frappe.db.get_single_value("ERPNext CRM Settings", "enabled"):
			frappe.throw(
				_(
					"ERPNext integration is active. Create an Item in ERPNext and it will appear here automatically."
				),
				title=_("Use ERPNext to Create Products"),
			)

	def validate(self):
		self.set_product_name()

	def set_product_name(self):
		if not self.product_name:
			self.product_name = self.product_code
		else:
			self.product_name = self.product_name.strip()

	def on_update(self):
		if self.flags.get("ignore_erpnext_sync"):
			return
		if not self.get("erpnext_item_code"):
			return
		if not frappe.db.get_single_value("ERPNext CRM Settings", "enabled"):
			return
		push_product_to_erpnext_item(self)


def push_product_to_erpnext_item(doc):
	try:
		from erpnext.crm.frappe_crm_api import update_item_from_crm_product
	except ImportError:
		return

	item_code = doc.get("erpnext_item_code")
	if not frappe.db.exists("Item", item_code):
		frappe.db.set_value("CRM Product", doc.name, "erpnext_item_code", None)
		return

	data = {
		"item_name": doc.product_name,
		"standard_rate": doc.standard_rate,
		"image": doc.image,
		"disabled": doc.disabled,
		"description": doc.description,
	}

	try:
		update_item_from_crm_product(item_code, data)
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			f"Error pushing CRM Product {doc.name} to ERPNext Item",
		)


def sync_item_to_crm_product(item_doc, method=None):
	"""Called from Item doc_events."""
	if item_doc.flags.get("ignore_crm_sync"):
		return
	if not frappe.db.get_single_value("ERPNext CRM Settings", "enabled"):
		return

	data = {
		"product_name": item_doc.item_name,
		"standard_rate": item_doc.standard_rate,
		"image": item_doc.image,
		"disabled": item_doc.disabled,
		"description": item_doc.description,
	}

	existing = frappe.db.get_value("CRM Product", {"erpnext_item_code": item_doc.item_code})
	if existing:
		frappe.db.set_value("CRM Product", existing, data)
		return

	product = frappe.new_doc("CRM Product")
	product.product_code = item_doc.item_code
	product.erpnext_item_code = item_doc.item_code
	product.update(data)
	product.flags.ignore_erpnext_sync = True
	product.insert(ignore_permissions=True)
