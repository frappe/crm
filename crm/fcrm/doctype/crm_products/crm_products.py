# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMProducts(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amount: DF.Currency
		autocomplete: DF.Autocomplete | None
		discount_amount: DF.Currency
		discount_percentage: DF.Percent
		net_amount: DF.Currency
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		product_code: DF.Link | None
		product_name: DF.Data
		qty: DF.Float
		rate: DF.Currency
	# end: auto-generated types

	pass


<<<<<<< HEAD
=======
@frappe.whitelist()
def get_product_rate_details(product_code: str, deal: str | None = None) -> dict:
	product = (
		frappe.db.get_value("CRM Product", product_code, ["product_name", "standard_rate"], as_dict=True)
		or {}
	)
	rate = _contextual_rate(product_code, deal) or product.get("standard_rate")
	return {"product_name": product.get("product_name"), "rate": rate}


def _contextual_rate(product_code: str, deal: str | None):
	"""Rate from the linked ERPNext Item, priced in the deal's context."""
	if not frappe.get_meta("CRM Product").has_field("erpnext_item_code"):
		return None
	item_code = frappe.db.get_value("CRM Product", product_code, "erpnext_item_code")
	if not item_code:
		return None
	return get_deal_product_rate(item_code, deal)


def _resolve_price_list(customer: str | None):
	"""Customer's default price list, else the default selling price list."""
	if customer and frappe.db.exists("Customer", customer):
		from erpnext.accounts.party import get_default_price_list

		if pl := get_default_price_list(frappe.get_cached_doc("Customer", customer)):
			return pl
	return frappe.db.get_single_value("Selling Settings", "selling_price_list")


def get_deal_product_rate(item_code: str, deal: str | None = None):
	"""Resolve a deal line rate the way ERPNext prices a quotation line."""
	if not frappe.db.exists("DocType", "Item Price"):
		return None
	customer = frappe.db.get_value("CRM Deal", deal, "erpnext_customer") if deal else None
	price_list = _resolve_price_list(customer)
	if not price_list:
		return None
	from erpnext.stock.get_item_details import get_item_price

	pctx = {
		"price_list": price_list,
		"customer": customer,
		"uom": frappe.db.get_value("Item", item_code, "stock_uom"),
		"transaction_date": frappe.utils.nowdate(),
	}
	rows = get_item_price(pctx, item_code)
	return rows[0].price_list_rate if rows else None


>>>>>>> a5955da3 (feat: price deal products from ERPNext context)
def create_product_details_script(doctype):
	name = "Product Details Script for " + doctype
	script = get_product_details_script(doctype)
	# Standard script is app-owned: keep it in sync with code on every migrate.
	if frappe.db.exists("CRM Form Script", name):
		if frappe.db.get_value("CRM Form Script", name, "script") != script:
			frappe.db.set_value("CRM Form Script", name, "script", script)
		return
	frappe.get_doc(
		{
			"doctype": "CRM Form Script",
			"name": name,
			"dt": doctype,
			"view": "Form",
			"script": script,
			"enabled": 1,
			"is_standard": 1,
		}
	).insert()


def get_product_details_script(doctype):
	doctype_class = "class " + doctype.replace(" ", "")

	return (
		doctype_class
		+ " {"
		+ """
  update_total() {
    let total = 0
    let total_qty = 0
    let net_total = 0
    let discount_applied = false

    this.doc.products.forEach((d) => {
      total += d.amount
      net_total += d.net_amount
      if (d.discount_percentage > 0) {
        discount_applied = true
      }
    })

    this.doc.total = total
    this.doc.net_total = net_total || total

    if (!net_total && discount_applied) {
      this.doc.net_total = net_total
    }
  }
}

class CRMProducts {
  products_add() {
    let row = this.doc.getRow('products')
    row.trigger('qty')
    this.doc.trigger('update_total')
  }

  products_remove() {
    this.doc.trigger('update_total')
  }

  async product_code(idx) {
    let row = this.doc.getRow('products', idx)

<<<<<<< HEAD
    let a = await call("frappe.client.get_value", {
        doctype: "CRM Product",
        filters: { name: row.product_code },
        fieldname: ["product_name", "standard_rate"],
=======
    let a = await call("crm.fcrm.doctype.crm_products.crm_products.get_product_rate_details", {
        product_code: row.product_code,
        deal: this.doc.name,
>>>>>>> a5955da3 (feat: price deal products from ERPNext context)
    })

    row.product_name = a.product_name
    if (a.standard_rate && !row.rate) {
        row.rate = a.standard_rate
        row.trigger("rate")
    }
  }

  qty(idx) {
    let row = this.doc.getRow('products', idx)
    row.amount = row.qty * row.rate
    row.trigger('discount_percentage', idx)
  }

  rate() {
    let row = this.doc.getRow('products')
    row.amount = row.qty * row.rate
    row.trigger('discount_percentage')
  }

  discount_percentage(idx) {
    let row = this.doc.getRow('products', idx)
    if (!row.discount_percentage) {
      row.net_amount = row.amount
      row.discount_amount = 0
    }
    if (row.discount_percentage && row.amount) {
      row.discount_amount = (row.discount_percentage / 100) * row.amount
      row.net_amount = row.amount - row.discount_amount
    }
    this.doc.trigger('update_total')
  }
}"""
	)
