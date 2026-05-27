import frappe
from erpnext.stock.doctype.item.item import Item

from crm.fcrm.doctype.crm_product.sync_utils import payload_differs
from crm.integrations.erpnext.utils import (
	CASCADE_FLAG,
	cascade_rename,
	in_cascade,
	set_links,
	should_sync,
	validate_rename_conflict,
)

CATALOGUE_FIELDS = ("standard_rate", "image", "disabled", "description")


class CustomItem(Item):
	def after_insert(self):
		super().after_insert()
		if not self._should_sync():
			return
		if frappe.db.get_value("CRM Product", {"erpnext_item_code": self.name}):
			return
		product = frappe.get_doc(
			{
				"doctype": "CRM Product",
				"product_code": self.item_code,
				"product_name": self.item_name,
				**{f: self.get(f) for f in CATALOGUE_FIELDS},
			}
		)
		product.flags.ignore_erpnext_sync = True
		product.insert(ignore_permissions=True)
		set_links(self.name, product.name)

	def on_update(self):
		super().on_update()
		if not self._should_sync():
			return
		product_name = frappe.db.get_value("CRM Product", {"erpnext_item_code": self.name})
		if not product_name:
			return
		data = {
			"product_name": self.item_name,
			**{f: self.get(f) for f in CATALOGUE_FIELDS},
		}
		current = frappe.db.get_value("CRM Product", product_name, list(data.keys()), as_dict=True) or {}
		if not payload_differs(data, current):
			return
		frappe.db.set_value("CRM Product", product_name, data)

	def before_rename(self, olddn, newdn, merge=False):
		super().before_rename(olddn, newdn, merge)
		validate_rename_conflict("Item", olddn, newdn, merge)

	def after_rename(self, olddn, newdn, merge=False):
		super().after_rename(olddn, newdn, merge)
		cascade_rename("Item", olddn, newdn, merge)

	def on_trash(self):
		super().on_trash()
		if in_cascade() or not self._should_sync():
			return
		product = frappe.db.get_value("CRM Product", {"erpnext_item_code": self.name})
		if not product:
			return
		# Clear back link first so CRMProduct.on_trash won't try to delete this Item
		frappe.db.set_value("CRM Product", product, "erpnext_item_code", None)
		frappe.flags[CASCADE_FLAG] = True
		try:
			frappe.delete_doc("CRM Product", product, ignore_permissions=True)
		finally:
			frappe.flags[CASCADE_FLAG] = False

	def _should_sync(self) -> bool:
		return should_sync() and not self.flags.get("ignore_crm_sync")
