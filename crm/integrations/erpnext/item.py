import frappe
from erpnext.stock.doctype.item.item import Item

from crm.fcrm.doctype.crm_product.sync_utils import payload_differs, same_site_sync_active

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
				"erpnext_item_code": self.item_code,
				**{f: self.get(f) for f in CATALOGUE_FIELDS},
			}
		)
		product.flags.ignore_erpnext_sync = True
		product.insert(ignore_permissions=True)
		frappe.db.set_value("Item", self.name, "crm_product_code", product.name)

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
		current = (
			frappe.db.get_value("CRM Product", product_name, list(data.keys()), as_dict=True) or {}
		)
		if not payload_differs(data, current):
			return
		frappe.db.set_value("CRM Product", product_name, data)

	def after_rename(self, olddn, newdn, merge=False):
		super().after_rename(olddn, newdn, merge)
		if not self._should_sync():
			return
		product = frappe.db.get_value("CRM Product", {"erpnext_item_code": olddn})
		if product:
			frappe.db.set_value("CRM Product", product, "erpnext_item_code", newdn)

	def on_trash(self):
		super().on_trash()
		if not self._should_sync():
			return
		product = frappe.db.get_value("CRM Product", {"erpnext_item_code": self.name})
		if product:
			frappe.db.set_value("CRM Product", product, "erpnext_item_code", None)

	def _should_sync(self) -> bool:
		return same_site_sync_active() and not self.flags.get("ignore_crm_sync")
