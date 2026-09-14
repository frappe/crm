"""Daily snapshot of which features a site has configured and how much it uses them."""

import frappe
from frappe.utils import add_days, nowdate
from frappe.utils.telemetry import capture, is_pulse_enabled


def capture_feature_state():
	"""Emit one `crm_feature_state` event per site per day."""
	if not is_pulse_enabled():
		return

	properties = {}

	for collect in (lead_sync_state, product_sync_state, sales_hierarchy_state):
		try:
			properties.update(collect())
		except Exception:
			frappe.log_error(f"Feature state telemetry failed: {collect.__name__}")

	if properties:
		capture("crm_feature_state", "crm", properties=properties, interval="1d")


def lead_sync_state() -> dict:
	sources = frappe.get_all("Lead Sync Source", fields=["type", "enabled"])
	enabled_types = {s.type for s in sources if s.enabled}

	return {
		"lead_sync_enabled": bool(enabled_types),
		"lead_sync_sources": len(sources),
		"lead_sync_source_types": sorted(enabled_types),
		"leads_synced_total": count_synced_leads(),
		"leads_synced_30d": count_synced_leads(days=30),
	}


def count_synced_leads(days: int | None = None) -> int:
	filters = {"facebook_lead_id": ["is", "set"]}
	if days:
		filters["creation"] = [">", add_days(nowdate(), -days)]

	return frappe.db.count("CRM Lead", filters)


def product_sync_state() -> dict:
	settings = frappe.get_cached_doc("ERPNext CRM Settings")

	state = {
		"erpnext_sync_enabled": bool(settings.enabled),
		"products_sync_enabled": bool(settings.sync_products),
		"products_total": frappe.db.count("CRM Product"),
		"product_sync_issues_open": frappe.db.count("CRM Product Sync Issue", {"dismissed": 0}),
	}

	# erpnext_item_code is a custom field, added only once the integration is enabled
	if frappe.db.has_column("CRM Product", "erpnext_item_code"):
		state["products_synced_total"] = frappe.db.count("CRM Product", {"erpnext_item_code": ["is", "set"]})

	return state


def sales_hierarchy_state() -> dict:
	return {
		"sales_hierarchy_enabled": bool(
			frappe.db.get_single_value("FCRM Settings", "enable_sales_hierarchy")
		),
		"sales_hierarchy_nodes": frappe.db.count("CRM Sales Hierarchy"),
	}
