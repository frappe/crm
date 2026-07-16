# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from crm.fcrm.doctype.crm_product.sync_utils import payload_differs
from crm.integrations.erpnext.utils import (
	cascade_rename,
	in_cascade,
	should_push_to_erpnext,
	validate_rename_conflict,
)

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

	def before_insert(self):
		if self.flags.get("ignore_erpnext_sync"):
			return
		if should_push_to_erpnext():
			frappe.throw(
				_(
					"ERPNext integration is active. Create an Item in ERPNext and it will appear in CRM Product automatically."
				),
				title=_("Use ERPNext to Create Products"),
			)

	def validate(self):
		self.set_product_name()

	def set_product_name(self):
		self.product_name = (self.product_name or self.product_code or "").strip()

	def on_update(self):
		if self.flags.get("ignore_erpnext_sync"):
			return
		if not self.get("erpnext_item_code"):
			return
		if not should_push_to_erpnext():
			return
		_push_to_item(self)

	def before_rename(self, olddn, newdn, merge=False):
		validate_rename_conflict("CRM Product", olddn, newdn, merge)

	def after_rename(self, olddn, newdn, merge=False):
		cascade_rename("CRM Product", olddn, newdn, merge)

	def on_trash(self):
		if in_cascade():
			return
		if not self.get("erpnext_item_code"):
			return
		if not should_push_to_erpnext():
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
