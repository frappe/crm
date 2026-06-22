import frappe

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


def _should_sync(doc) -> bool:
	return should_sync() and not doc.flags.get("ignore_crm_sync")


def get_item_price_rate(item_code: str):
	"""Fall back to the latest valid selling Item Price when standard_rate is null."""
	return frappe.db.get_value(
		"Item Price",
		{"item_code": item_code, "selling": 1},
		"price_list_rate",
		order_by="valid_from desc",
	)


def _catalogue_data(doc) -> dict:
	data = {f: doc.get(f) for f in CATALOGUE_FIELDS}
	if not data.get("standard_rate"):
		data["standard_rate"] = get_item_price_rate(doc.name)
	return data


def after_insert(doc, method=None):
	if not _should_sync(doc):
		return
	if frappe.db.get_value("CRM Product", {"erpnext_item_code": doc.name}):
		return
	product = frappe.get_doc(
		{
			"doctype": "CRM Product",
			"product_code": doc.item_code,
			"product_name": doc.item_name,
			**_catalogue_data(doc),
		}
	)
	product.flags.ignore_erpnext_sync = True
	product.insert(ignore_permissions=True)
	set_links(doc.name, product.name)


def on_update(doc, method=None):
	if not _should_sync(doc):
		return
	product_name = frappe.db.get_value("CRM Product", {"erpnext_item_code": doc.name})
	if not product_name:
		return
	data = {
		"product_name": doc.item_name,
		**_catalogue_data(doc),
	}
	current = frappe.db.get_value("CRM Product", product_name, list(data.keys()), as_dict=True) or {}
	if not payload_differs(data, current):
		return
	frappe.db.set_value("CRM Product", product_name, data)


def before_rename(doc, method=None, olddn=None, newdn=None, merge=False):
	validate_rename_conflict("Item", olddn, newdn, merge)


def after_rename(doc, method=None, olddn=None, newdn=None, merge=False):
	cascade_rename("Item", olddn, newdn, merge)


def on_trash(doc, method=None):
	if in_cascade() or not _should_sync(doc):
		return
	product = frappe.db.get_value("CRM Product", {"erpnext_item_code": doc.name})
	if not product:
		return
	# Clear back link first so CRMProduct.on_trash won't try to delete this Item
	frappe.db.set_value("CRM Product", product, "erpnext_item_code", None)
	frappe.flags[CASCADE_FLAG] = True
	try:
		frappe.delete_doc("CRM Product", product, ignore_permissions=True)
	finally:
		frappe.flags[CASCADE_FLAG] = False
