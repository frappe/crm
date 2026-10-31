# Quotes

The CRM doesn't make quotes on its own. A quote is an ERPNext Quotation, made from a deal. ERPNext is Frappe's accounting app. It can be on the same site as the CRM, or on another site that the CRM connects to.

Before anything else, call `setup_status` and read `quotes`:

- `erpnext_on_this_site`: whether ERPNext is installed on this site.
- `connected`: whether the CRM is connected to ERPNext, here or on another site.
- `erpnext_site`: the other site's address, if ERPNext is on another site.
- `can_create`: whether this person may make quotations.

## ERPNext isn't there yet

When `connected` is false and `erpnext_on_this_site` is false, say in plain words that quotes are made in ERPNext, which isn't on their site yet, and give them two ways:

- **Install ERPNext on this site.** On Frappe Cloud, the site's owner opens the site in the Frappe Cloud dashboard, goes to Apps and installs ERPNext. You can't install apps from this chat.
- **Connect an ERPNext site they already have** in [ERPNext settings](/crm/deals?settings=ERPNext), with that site's address and an API key.

Link the guide: https://docs.frappe.io/crm/erpnext. Options: I'll install ERPNext, I have an ERPNext site, Not now. Don't offer to make the deal or its products ready for a quote until one of these is done.

## ERPNext is installed but not connected

When `erpnext_on_this_site` is true and `connected` is false, ERPNext only needs switching on: [ERPNext settings](/crm/deals?settings=ERPNext), turn on the integration and pick the company the quotes come from. Only a Sales Manager or admin can do this, so if they can't open it, they need to ask one.

## Ready for quotes

When `connected` is true:

1. If `can_create` is false, say they don't have permission to make quotations and their admin can give it to them. Stop there.
2. Ask which deal the quote is for, unless it's clear. Look it up with `read_records`.
3. If they list what to quote, it goes on the deal's Products first. Check the products exist with `read_records("CRM Product", ...)` and read each one's `product_name` and `standard_rate`. Each row needs `product_code`, `product_name` (the product's name, or its code when it has none), `qty`, `rate` (their price, else the standard rate) and an optional `discount_percentage`. The deal page usually fills in the rest, but `update` doesn't run it, so also set `amount` (qty × rate), `discount_amount` (amount × discount ÷ 100), `net_amount` (amount − discount_amount), and the deal's `total` and `net_total` (the sums over every row). Add the rows with `update` on the deal's `products` table, keeping the rows already there. Products that came from ERPNext carry over to the quote; others don't, so say so.
4. Then give them the deal as a link, such as [Open the Corvid deal](/crm/deals/CRM-DEAL-2026-00004), and say: click **Create Quotation** on the deal. ERPNext opens a new quotation filled in with the deal's customer, contact, address and products. They check the prices and save it there. It then shows on the deal's Quotations tab.

Don't create Quotation records yourself, even when ERPNext is on this site. The deal's button fills in the customer and contact the way ERPNext expects.
