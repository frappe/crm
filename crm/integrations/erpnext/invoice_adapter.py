"""
invoice_adapter.py — create ERPNext Sales Invoice from an accepted Quotation.

Uses ERPNext's native make_sales_invoice mapper so line items, taxes, customer,
and pricing are all propagated natively. Adds CRM back-link fields (crm_deal,
crm_quotation) to the resulting Sales Invoice for Finance Cockpit traceability.
"""
import frappe


def _resolve_item_code(crm_sku):
	"""Return the ERPNext item_code linked to a CRM Product, falling back to crm_sku."""
	if not crm_sku:
		return crm_sku
	erpnext_code = frappe.db.get_value("CRM Product", crm_sku, "erpnext_item_code")
	if erpnext_code and frappe.db.exists("Item", erpnext_code):
		return erpnext_code
	return crm_sku


def _item_uom(item_code):
	return frappe.db.get_value("Item", item_code, "stock_uom") or "Nos"


def create_sales_invoice_from_quotation(quotation_name):
	"""
	Create an ERPNext Sales Invoice from a submitted (docstatus=1) Quotation.
	Uses the native ERPNext mapper so all item, tax, and customer data is
	propagated correctly. Sets crm_deal and crm_quotation back-link fields.
	Returns {"invoice_name": str}.
	SYSTEM-INTERNAL
	"""
	if not frappe.db.exists("DocType", "Sales Invoice"):
		frappe.throw("ERPNext Sales Invoice DocType not available on this site")

	from erpnext.selling.doctype.quotation.quotation import make_sales_invoice

	# make_sales_invoice requires docstatus=1
	if frappe.db.get_value("Quotation", quotation_name, "docstatus") != 1:
		frappe.throw("Quotation %s must be submitted (docstatus=1) before creating a Sales Invoice" % quotation_name)

	si_dict = make_sales_invoice(quotation_name)
	si = frappe.get_doc(si_dict)

	# Set CRM back-links
	crm_deal = frappe.db.get_value("Quotation", quotation_name, "crm_deal")
	si.crm_deal        = crm_deal
	si.crm_quotation   = quotation_name

	si.flags.ignore_validate    = True
	si.flags.ignore_permissions = True  # SYSTEM-INTERNAL
	si.insert(ignore_mandatory=True)

	frappe.db.commit()
	return {"invoice_name": si.name}


# Kept for backward compatibility — any old CRM Quote records that were accepted
# before the migration will already have a Sales Invoice. This path is no longer
# called for new quotes.
def create_sales_invoice(quote):
	"""Legacy path for CRM Quote acceptance (pre-migration). No longer used for new quotes."""
	frappe.log_error(
		"create_sales_invoice called on legacy CRM Quote %s — should use create_sales_invoice_from_quotation" % quote.name,
		"invoice_adapter.legacy",
	)
	return {"invoice_name": ""}
