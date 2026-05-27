import frappe
from frappe import _

from crm.fcrm.doctype.crm_product.reconciliation import (
	CATALOGUE_FIELDS,
	classify_pair,
	detect_orphan,
)


def enqueue_reconciliation():
	frappe.enqueue(
		"crm.fcrm.doctype.crm_product.reconcile_job.run_reconciliation",
		queue="long",
		timeout=1200,
		job_id="crm_product_item_reconciliation",
		deduplicate=True,
	)


def run_reconciliation() -> dict:
	if not frappe.db.exists("DocType", "Item"):
		return {"skipped": "erpnext_not_installed"}

	settings = frappe.get_single("ERPNext CRM Settings")
	if not settings.enabled:
		return {"skipped": "integration_disabled"}
	if settings.is_erpnext_in_different_site:
		return {"skipped": "cross_site_not_supported"}

	summary = {
		"already_linked": 0,
		"linked_by_exact_code": 0,
		"created_in_crm": 0,
		"created_in_erpnext": 0,
		"unlinked_orphans": 0,
	}

	items = {
		i["item_code"]: i
		for i in frappe.db.get_all(
			"Item",
			fields=[
				"item_code",
				"item_name",
				"standard_rate",
				"image",
				"disabled",
				"description",
				"crm_product_code",
			],
		)
	}
	products = {
		p["product_code"]: p
		for p in frappe.db.get_all(
			"CRM Product",
			fields=[
				"name",
				"product_code",
				"product_name",
				"standard_rate",
				"image",
				"disabled",
				"description",
				"erpnext_item_code",
			],
		)
	}

	issues = []

	for code, item in items.items():
		product = products.get(code)
		if not product:
			_create_crm_product_from_item(item)
			summary["created_in_crm"] += 1
			continue
		action = classify_pair(item, product)
		if action.rule == "already_linked":
			summary["already_linked"] += 1
		else:
			summary["linked_by_exact_code"] += 1
		if action.crm_updates:
			frappe.db.set_value("CRM Product", product["name"], action.crm_updates)
		if action.item_updates:
			frappe.db.set_value("Item", item["item_code"], action.item_updates)

	existing_item_codes = set(items.keys())

	for code, product in products.items():
		if code in existing_item_codes:
			continue
		if detect_orphan(product, existing_item_codes):
			frappe.db.set_value("CRM Product", product["name"], "erpnext_item_code", None)
			issues.append(
				{
					"product": product["name"],
					"kind": "unlinked_orphan",
					"detail": _("Linked Item {0} no longer exists").format(product["erpnext_item_code"]),
				}
			)
			summary["unlinked_orphans"] += 1
			continue
		if product.get("erpnext_item_code"):
			continue
		doc = frappe.get_doc("CRM Product", product["name"])
		_create_item_from_product(doc)
		summary["created_in_erpnext"] += 1

	_record_issues(settings, issues)
	frappe.publish_realtime("crm_product_sync_complete", user=frappe.session.user)
	frappe.log_error(message=frappe.as_json(summary), title="CRM Product Reconciliation")
	return summary


def _create_crm_product_from_item(item):
	product = frappe.new_doc("CRM Product")
	product.product_code = item["item_code"]
	product.erpnext_item_code = item["item_code"]
	product.product_name = item.get("item_name")
	for f in CATALOGUE_FIELDS:
		product.set(f, item.get(f))
	product.flags.ignore_erpnext_sync = True
	product.insert(ignore_permissions=True)
	frappe.db.set_value("Item", item["item_code"], "crm_product_code", product.name)


def _create_item_from_product(product_doc):
	item = frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": product_doc.product_code,
			"item_name": product_doc.product_name or product_doc.product_code,
			"standard_rate": product_doc.standard_rate,
			"image": product_doc.image,
			"disabled": product_doc.disabled,
			"description": product_doc.description,
			"crm_product_code": product_doc.name,
			"item_group": frappe.db.get_single_value("Stock Settings", "item_group") or "All Item Groups",
			"stock_uom": frappe.db.get_single_value("Stock Settings", "stock_uom") or "Nos",
			"is_stock_item": 0,
		}
	)
	item.flags.ignore_crm_sync = True
	item.insert(ignore_permissions=True)
	frappe.db.set_value("CRM Product", product_doc.name, "erpnext_item_code", item.name)


def _record_issues(settings, issues):
	if not issues:
		return
	for issue in issues:
		settings.append("sync_issues", issue)
	settings.save(ignore_permissions=True)
