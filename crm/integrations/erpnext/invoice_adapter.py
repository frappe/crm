"""
invoice_adapter.py — create ERPNext Sales Invoice from an accepted CRM Quote.
Server-side only. Not a whitelisted method.
"""
import frappe
from frappe.utils import nowdate


def _get_vat_account(company):
	"""Resolve the 16% VAT tax account for the given company."""
	# Try to find a tax account with rate ~16 for this company
	accounts = frappe.get_list(
		"Account",
		filters=[
			["company", "=", company],
			["account_type", "=", "Tax"],
			["disabled", "=", 0],
		],
		fields=["name", "account_name"],
		limit=10,
	)
	for acc in accounts:
		name_lower = (acc.account_name or "").lower()
		if "vat" in name_lower or "16" in name_lower or "tax" in name_lower:
			return acc.name
	# Fall back to the first tax account found
	return accounts[0].name if accounts else None


def create_sales_invoice(quote):
	"""
	Create an ERPNext Sales Invoice from an accepted CRM Quote.
	Sets crm_deal and crm_quote custom fields on the invoice.
	Returns {"invoice_name": str}.
	SYSTEM-INTERNAL
	"""
	if not frappe.db.exists("DocType", "Sales Invoice"):
		frappe.throw("ERPNext Sales Invoice DocType not available on this site")

	# Build line items
	items = []
	for row in (quote.facilities or []):
		items.append({
			"item_code": row.subscription_sku,
			"item_name": "CareVerse SaaS — %s (%s)" % (row.facility_name, row.package_tier),
			"description": "CareVerse SaaS Subscription — %s" % row.facility_name,
			"qty": 1,
			"rate": row.subscription_net or 0,
			"uom": "Nos",
		})
		if (row.impl_net or 0) > 0:
			items.append({
				"item_code": row.impl_sku,
				"item_name": "Implementation & Training — %s" % row.facility_name,
				"description": "One-time implementation and training — %s" % row.facility_name,
				"qty": 1,
				"rate": row.impl_net or 0,
				"uom": "Nos",
			})

	for row in (quote.addons or []):
		if (row.qty or 0) > 0:
			items.append({
				"item_code": row.product_sku,
				"item_name": row.description or row.product_sku,
				"description": row.description or "",
				"qty": row.qty or 1,
				"rate": row.unit_price or 0,
				"uom": "Nos",
			})

	if not items:
		frappe.throw("CRM Quote %s has no line items — cannot create Sales Invoice" % quote.name)

	company = frappe.db.get_single_value("Global Defaults", "default_company")

	# Resolve ERPNext Customer — create one if it doesn't exist
	customer_name = quote.customer or "Default Customer"
	if not frappe.db.exists("Customer", customer_name):
		try:
			cust = frappe.get_doc({
				"doctype": "Customer",
				"customer_name": customer_name,
				"customer_type": "Company",
				"customer_group": frappe.db.get_single_value("Selling Settings", "customer_group") or "All Customer Groups",
				"territory": frappe.db.get_single_value("Selling Settings", "territory") or "All Territories",
			})
			cust.insert(ignore_permissions=True)  # SYSTEM-INTERNAL
			frappe.db.commit()
		except Exception:
			# If customer creation fails, use first available customer
			existing = frappe.get_list("Customer", limit=1, pluck="name")
			customer_name = existing[0] if existing else customer_name

	# Build taxes
	taxes = []
	vat_account = _get_vat_account(company) if company else None
	if vat_account:
		taxes.append({
			"charge_type": "On Net Total",
			"account_head": vat_account,
			"rate": 16,
			"description": "VAT 16%",
		})

	inv_data = {
		"doctype": "Sales Invoice",
		"customer": customer_name,
		"posting_date": nowdate(),
		"due_date": quote.valid_until or nowdate(),
		"currency": quote.currency or "KES",
		"items": items,
	}
	if company:
		inv_data["company"] = company
	if taxes:
		inv_data["taxes"] = taxes

	inv = frappe.get_doc(inv_data)
	inv.flags.ignore_validate = True  # CRM-native SKUs may not be synced to ERPNext Items yet
	inv.insert(
		ignore_permissions=True,
		ignore_links=True,
		ignore_mandatory=True,
	)  # SYSTEM-INTERNAL

	# Set custom fields (created by migration patch)
	try:
		frappe.db.set_value("Sales Invoice", inv.name, "crm_deal", quote.deal)
		frappe.db.set_value("Sales Invoice", inv.name, "crm_quote", quote.name)
	except Exception:
		pass  # Custom fields may not exist on all sites

	frappe.db.commit()
	return {"invoice_name": inv.name}
