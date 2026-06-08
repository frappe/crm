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


@frappe.whitelist()
def get_product_rate_details(product_code: str) -> dict:
	product = (
		frappe.db.get_value("CRM Product", product_code, ["product_name", "standard_rate"], as_dict=True)
		or {}
	)
	rate = _item_price_rate(product_code) or product.get("standard_rate")
	return {"product_name": product.get("product_name"), "rate": rate}


def _item_price_rate(product_code: str):
	"""Latest valid selling Item Price for the linked ERPNext Item"""
	if not frappe.get_meta("CRM Product").has_field("erpnext_item_code"):
		return None
	item_code = frappe.db.get_value("CRM Product", product_code, "erpnext_item_code")
	if not item_code or not frappe.db.exists("DocType", "Item Price"):
		return None
	from crm.integrations.erpnext.item import get_item_price_rate

	return get_item_price_rate(item_code)


def create_product_details_script(doctype):
	if not frappe.db.exists("CRM Form Script", "Product Details Script for " + doctype):
		script = get_product_details_script(doctype)
		frappe.get_doc(
			{
				"doctype": "CRM Form Script",
				"name": "Product Details Script for " + doctype,
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

    let a = await call("crm.fcrm.doctype.crm_products.crm_products.get_product_rate_details", {
        product_code: row.product_code,
    })
    if (!a) return

    row.product_name = a.product_name
    if (a.rate && !row.rate) {
        row.rate = a.rate
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
