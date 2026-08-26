"""
crm/api/quotes.py — Quote lifecycle API targeting ERPNext Quotation doctype.

All whitelisted method paths are unchanged from the CRM Quote era so the
Vue frontend requires no URL changes.

Lifecycle mapping:
  Draft   = Quotation docstatus=0
  Sent    = Quotation docstatus=0  +  crm_sent=1
  Accepted = Quotation docstatus=1  (submit)
  Rejected = Quotation docstatus=2  (cancel)

CRM-specific data stored on Quotation via custom fields:
  crm_deal, crm_partner, crm_payment_terms, contract_term_yrs,
  contract_start_date, crm_sent, previous_version, discount_applied,
  vat_amount, renewal_schedule (Table → CRM Quote Renewal Schedule)

Pricing follows ERPNext's native Item Price architecture: each line's default
rate is the price_list_rate on the quote's selling_price_list (Standard Selling
by default; Negotiated Year 1-5 for multi-year deals). The exec negotiates each
line rate manually on top of that default — there is no automated tier/discount
compute engine.

Line items stored as QuotationItem rows:
  - item_code = an ERPNext Item, qty, rate = negotiated unit price
  - facility_name / package_tier custom fields carry OIS provenance when present
"""
import json
import frappe
from frappe.utils import nowdate, add_days, getdate, date_diff

VAT_RATE       = 0.16
DEFAULT_PRICE_LIST = "Standard Selling"

# Frontend-facing status values derived from docstatus + crm_sent
_STATUS_ACCEPTED = "Accepted"
_STATUS_REJECTED = "Rejected"
_STATUS_SENT     = "Sent"
_STATUS_DRAFT    = "Draft"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _is_admin(roles):
	return "System Manager" in roles or frappe.session.user == "Administrator"


def _resolve_item_code(crm_sku):
	"""Return the ERPNext item_code linked to a CRM Product, falling back to the sku itself."""
	if not crm_sku:
		return crm_sku
	erpnext_code = frappe.db.get_value("CRM Product", crm_sku, "erpnext_item_code")
	if erpnext_code and frappe.db.exists("Item", erpnext_code):
		return erpnext_code
	return crm_sku


def _item_uom(item_code):
	return frappe.db.get_value("Item", item_code, "stock_uom") or "Nos"


def _get_item_price(item_code, price_list):
	"""
	Return the selling price_list_rate for an Item on a given Price List, honouring
	Item Price validity dates. Falls back to the default Standard Selling list, then 0.
	This is the single source of default line pricing (ERPNext Item Price architecture).
	"""
	if not item_code:
		return 0.0

	def _lookup(pl):
		rows = frappe.get_list(
			"Item Price",
			filters=[
				["item_code", "=", item_code],
				["price_list", "=", pl],
				["selling", "=", 1],
			],
			fields=["price_list_rate", "valid_from", "valid_upto"],
			order_by="valid_from desc",
			limit_page_length=0,
		)
		today = getdate(nowdate())
		for r in rows:
			vf = getdate(r.valid_from) if r.valid_from else None
			vu = getdate(r.valid_upto) if r.valid_upto else None
			if (vf is None or vf <= today) and (vu is None or vu >= today):
				return float(r.price_list_rate or 0)
		# no date-valid row → fall back to the newest row regardless of dates
		return float(rows[0].price_list_rate) if rows else None

	rate = _lookup(price_list) if price_list else None
	if rate is None and price_list != DEFAULT_PRICE_LIST:
		rate = _lookup(DEFAULT_PRICE_LIST)
	return float(rate or 0)


def _derive_status(doc):
	"""Map ERPNext docstatus + crm_sent to the frontend-facing status string."""
	ds = int(doc.get("docstatus") or 0)
	if ds == 1:
		return _STATUS_ACCEPTED
	if ds == 2:
		return _STATUS_REJECTED
	if doc.get("crm_sent"):
		return _STATUS_SENT
	return _STATUS_DRAFT


def _ensure_customer(customer_name):
	"""
	Resolve an ERPNext Customer for a CRM Deal, creating it if absent. Deals with
	no organisation fall back to a "Default Customer" that is likewise created on
	demand — so create_quote never fails on a missing party.
	"""
	target = customer_name or "Default Customer"
	if frappe.db.exists("Customer", target):
		return target
	try:
		cust = frappe.get_doc({
			"doctype": "Customer",
			"customer_name": target,
			"customer_type": "Company",
			"customer_group": frappe.db.get_single_value("Selling Settings", "customer_group") or "All Customer Groups",
			"territory": frappe.db.get_single_value("Selling Settings", "territory") or "All Territories",
		})
		cust.insert(ignore_permissions=True)  # SYSTEM-INTERNAL
		frappe.db.commit()
		return target
	except Exception:
		existing = frappe.get_list("Customer", limit=1, pluck="name")
		return existing[0] if existing else target


def _apply_manual_rates(doc, rates):
	"""
	Make the exec's manual line rates authoritative. ERPNext's set_missing_values()
	re-fetches price_list_rate for any zero/unset rate, which would clobber a
	deliberately negotiated rate — including a waived 0 (free line). Call this AFTER
	set_missing_values() and BEFORE calculate_taxes_and_totals(), passing rates in
	doc.items order, so the "purely manual" rate always wins.
	"""
	doc.ignore_pricing_rule = 1
	for row, rate in zip(doc.items or [], rates):
		rate = float(rate or 0)
		row.price_list_rate      = rate
		row.rate                 = rate
		row.margin_type          = ""
		row.margin_rate_or_amount = 0
		row.rate_with_margin     = 0
		row.discount_percentage  = 0
		row.discount_amount      = 0



# ── Whitelisted API methods ────────────────────────────────────────────────────

def _require_manager():
	"""Gate mutating quote actions to Sales Manager / System Manager / Administrator."""
	roles = frappe.get_roles(frappe.session.user)
	if not (_is_admin(roles) or "Sales Manager" in roles):
		frappe.throw("Not permitted: requires Sales Manager or System Manager", frappe.PermissionError)


@frappe.whitelist()
def create_quote(deal, price_list=None):
	"""
	Create a blank Draft Quotation for a CRM Deal and return its name. This is the
	single entry point for starting a quote on any deal (OIS deals auto-build via
	crm.api.optin.build_ois_quote; non-OIS deals call this). The exec then adds
	catalogue lines and negotiates rates inline via save_quote_lines.
	"""
	_require_manager()
	if not frappe.db.exists("CRM Deal", deal):
		frappe.throw("CRM Deal not found: %s" % deal)

	price_list = price_list or DEFAULT_PRICE_LIST
	customer_name = _ensure_customer(frappe.db.get_value("CRM Deal", deal, "organization") or "")

	doc = frappe.get_doc({
		"doctype": "Quotation",
		"quotation_to": "Customer",
		"party_name":   customer_name,
		"company":      frappe.db.get_single_value("Global Defaults", "default_company"),
		"transaction_date": nowdate(),
		"valid_till":   add_days(nowdate(), 30),
		"currency":     "KES",
		"selling_price_list": price_list,
		"order_type":   "Sales",
		"crm_deal":     deal,
		"crm_payment_terms": "Annual Upfront",
		"vat_amount":   0,
		"items":        [],
	})
	doc.flags.ignore_permissions = True  # SYSTEM-INTERNAL
	doc.flags.ignore_validate    = True
	doc.flags.ignore_mandatory   = True
	doc.set_missing_values()
	doc.insert(ignore_mandatory=True, ignore_permissions=True)
	frappe.db.commit()
	return {"name": doc.name, "status": _derive_status(doc), "price_list": price_list}


@frappe.whitelist()
def list_quotes(deal):
	"""Return all Quotations for a given CRM Deal, shaped for the QuotingTab."""
	rows = frappe.get_list(
		"Quotation",
		filters=[["crm_deal", "=", deal]],
		fields=[
			"name", "transaction_date as quote_date", "valid_till as valid_until",
			"contract_start_date", "grand_total", "docstatus", "crm_sent",
			"crm_payment_terms as payment_terms", "contract_term_yrs",
			"previous_version", "currency", "creation",
		],
		order_by="creation desc",
	)
	# Derive frontend status from docstatus + crm_sent
	for r in rows:
		r["status"] = _derive_status(r)
		r["erpnext_sales_invoice"] = _invoice_for_quotation(r["name"])
	return rows


def _invoice_for_quotation(quotation_name):
	"""Return the first Sales Invoice name linked to this Quotation, if any."""
	rows = frappe.get_list(
		"Sales Invoice",
		filters=[["crm_quotation", "=", quotation_name]],
		pluck="name",
		limit=1,
	)
	return rows[0] if rows else None


@frappe.whitelist()
def list_all_quotes(status=None, from_date=None, to_date=None, search=None, page=0, page_size=20):
	"""Paginated global Quotation list with RBAC scoping."""
	roles = frappe.get_roles(frappe.session.user)
	user  = frappe.session.user
	filters = []

	if not (_is_admin(roles) or "Finance Manager" in roles or "Accounts Manager" in roles):
		if "Sales Manager" in roles:
			team_users = frappe.get_list(
				"User", filters=[["name", "!=", "Administrator"]], pluck="name", limit=500
			)
			team_deals = frappe.get_list(
				"CRM Deal", filters=[["deal_owner", "in", team_users]], pluck="name", limit=2000,
			) or ["__none__"]
			filters.append(["crm_deal", "in", team_deals])
		elif "Partner RM" in roles:
			own_partners = frappe.get_list(
				"CRM Partner", filters={"partner_rm": user}, pluck="name"
			) or ["__none__"]
			partner_deals = frappe.get_list(
				"CRM Deal", filters=[["partner", "in", own_partners]], pluck="name", limit=2000,
			) or ["__none__"]
			filters.append(["crm_deal", "in", partner_deals])
		else:
			own_deals = frappe.get_list(
				"CRM Deal", filters={"deal_owner": user}, pluck="name"
			) or ["__none__"]
			filters.append(["crm_deal", "in", own_deals])

	# Status filtering — map frontend status tokens to docstatus / crm_sent
	if status and status not in ("All",):
		if status == "Draft":
			filters += [["docstatus", "=", 0], ["crm_sent", "=", 0]]
		elif status == "Sent":
			filters += [["docstatus", "=", 0], ["crm_sent", "=", 1]]
		elif status == "Accepted":
			filters.append(["docstatus", "=", 1])
		elif status == "Rejected":
			filters.append(["docstatus", "=", 2])
		elif status == "Expired":
			filters += [["docstatus", "=", 0], ["valid_till", "<", nowdate()]]

	if from_date:
		filters.append(["transaction_date", ">=", from_date])
	if to_date:
		filters.append(["transaction_date", "<=", to_date])
	if search:
		filters.append(["name", "like", "%%%s%%" % search])

	rows = frappe.get_list(
		"Quotation",
		filters=filters,
		fields=[
			"name", "crm_deal as deal", "party_name as customer", "crm_partner as partner",
			"transaction_date as quote_date", "valid_till as valid_until",
			"grand_total", "docstatus", "crm_sent",
			"crm_payment_terms as payment_terms", "contract_term_yrs",
			"owner", "creation",
		],
		order_by="transaction_date desc",
		limit_page_length=int(page_size),
		limit_start=int(page) * int(page_size),
	)

	for r in rows:
		r["status"] = _derive_status(r)
		r["erpnext_sales_invoice"] = _invoice_for_quotation(r["name"])

	total = frappe.db.count("Quotation", filters)
	kpis  = _quote_kpis()

	return {"rows": rows, "total": total, "kpis": kpis}


def _quote_kpis():
	try:
		from frappe.utils import get_first_day
		month_start = get_first_day(nowdate())

		draft_count = frappe.db.count("Quotation", [["docstatus", "=", 0], ["crm_sent", "=", 0]])
		sent_count  = frappe.db.count("Quotation", [["docstatus", "=", 0], ["crm_sent", "=", 1]])

		accepted_rows = frappe.get_list(
			"Quotation",
			filters=[["docstatus", "=", 1], ["transaction_date", ">=", month_start]],
			fields=[{"SUM": "grand_total", "as": "total"}],
			limit=1,
		)
		accepted_value = float((accepted_rows[0].total or 0) if accepted_rows else 0)

		pipeline_rows = frappe.get_list(
			"Quotation",
			filters=[["docstatus", "=", 0]],
			fields=[{"SUM": "grand_total", "as": "total"}],
			limit=1,
		)
		pipeline_value = float((pipeline_rows[0].total or 0) if pipeline_rows else 0)

		return {
			"draft_count": draft_count,
			"sent_count": sent_count,
			"accepted_this_month": accepted_value,
			"pipeline_value": pipeline_value,
		}
	except Exception:
		return {"draft_count": 0, "sent_count": 0, "accepted_this_month": 0, "pipeline_value": 0}


@frappe.whitelist()
def send_quote(quote_name):
	"""Email the quote PDF to the deal's primary contact and mark crm_sent=1."""
	doc = frappe.get_doc("Quotation", quote_name)
	if doc.docstatus != 0:
		frappe.throw("Can only send a Draft quote (not yet submitted or cancelled)")

	rep_name = frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user

	# Resolve recipient from the linked CRM Deal
	recipient_email = None
	deal_name = doc.get("crm_deal")
	if deal_name:
		deal = frappe.get_doc("CRM Deal", deal_name)
		for c in (deal.contacts or []):
			if c.is_primary:
				recipient_email = frappe.db.get_value("Contact", c.contact, "email_id")
				break
	if not recipient_email:
		recipient_email = frappe.db.get_value("Customer", doc.party_name, "customer_primary_email") or ""

	pdf_data = frappe.get_print("Quotation", quote_name, "Careverse Quote Standard", as_pdf=True)

	if recipient_email:
		frappe.sendmail(
			recipients=[recipient_email],
			subject="Quotation %s — Tiberbu CareVerse HMIS" % quote_name,
			message="Please find attached the quotation %s from Tiberbu Healthnet Solutions." % quote_name,
			attachments=[{"fname": "%s.pdf" % quote_name, "fcontent": pdf_data}],
			sender=frappe.db.get_single_value("Email Account", "email_id") or "sales@tiberbu.com",
			sender_full_name=rep_name,
			now=True,
		)

	frappe.db.set_value("Quotation", quote_name, "crm_sent", 1)
	frappe.db.commit()
	return {"status": "sent", "quote_name": quote_name, "sent_to": recipient_email or ""}


@frappe.whitelist()
def accept_quote(quote_name):
	"""
	Submit the Quotation (docstatus → 1) and create a Sales Invoice via the
	native ERPNext make_sales_invoice mapper.
	"""
	doc = frappe.get_doc("Quotation", quote_name)
	if doc.docstatus != 0 or not doc.get("crm_sent"):
		frappe.throw("Only Sent quotes (crm_sent=1, docstatus=0) can be accepted")

	doc.flags.ignore_permissions = True  # SYSTEM-INTERNAL
	doc.submit()
	frappe.db.commit()

	from crm.integrations.erpnext.invoice_adapter import create_sales_invoice_from_quotation
	result = create_sales_invoice_from_quotation(quote_name)
	invoice_name = result.get("invoice_name", "")

	return {"status": "accepted", "quote_name": quote_name, "invoice_name": invoice_name}


@frappe.whitelist()
def reject_quote(quote_name):
	"""Cancel the Quotation (docstatus → 2)."""
	doc = frappe.get_doc("Quotation", quote_name)
	if doc.docstatus == 1:
		frappe.throw("Accepted (submitted) quotes cannot be rejected. Cancel the Sales Invoice first.")
	if doc.docstatus == 2:
		frappe.throw("Quote is already cancelled")
	doc.flags.ignore_permissions = True  # SYSTEM-INTERNAL
	doc.cancel()
	frappe.db.commit()
	return {"status": "rejected", "quote_name": quote_name}


@frappe.whitelist()
def list_price_lists():
	"""Selling price lists offered in the quote editor's price-list selector."""
	rows = frappe.get_list(
		"Price List",
		filters=[["selling", "=", 1], ["enabled", "=", 1]],
		fields=["name", "currency"],
		order_by="name asc",
	)
	return [{"value": r.name, "label": r.name, "currency": r.currency} for r in rows]


@frappe.whitelist()
def set_quote_price_list(quote, price_list):
	"""
	Switch a Draft/Sent (docstatus=0) Quotation to another selling price list and
	re-default every line rate from that list's Item Price (ERPNext Item Price
	architecture). Exec-negotiated overrides are intentionally reset to the new
	list's baseline; the exec re-negotiates from there. Recomputes totals + VAT.
	"""
	_require_manager()

	doc = frappe.get_doc("Quotation", quote)
	if int(doc.docstatus or 0) != 0:
		frappe.throw("Cannot update price list on a submitted or cancelled Quotation")

	doc.selling_price_list = price_list
	# Re-baseline every line to the new list's Item Price. A true miss resolves to
	# 0 (via _get_item_price's Standard-Selling fallback) so the exec re-enters it.
	baseline_rates = [_get_item_price(row.item_code, price_list) for row in (doc.items or [])]

	doc.flags.ignore_permissions = True  # SYSTEM-INTERNAL
	doc.flags.ignore_validate    = True
	doc.flags.ignore_mandatory   = True
	doc.set_missing_values()
	_apply_manual_rates(doc, baseline_rates)
	doc.calculate_taxes_and_totals()
	doc.vat_amount = round((doc.net_total or 0) * VAT_RATE, 2)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"price_list":  price_list,
		"net_total":   float(doc.net_total or 0),
		"vat_amount":  float(doc.vat_amount or 0),
		"grand_total": float(doc.grand_total or 0),
	}


@frappe.whitelist()
def get_quote_lines(quote):
	"""
	Return the raw ordered QuotationItem rows of a Quotation for inline exec
	editing on the Deal → Quoting tab. Returns exactly what is stored — so
	OIS-sourced quotes with KEPH-level item codes render 1:1.
	"""
	doc = frappe.get_doc("Quotation", quote)

	lines = []
	for it in (doc.items or []):
		qty  = float(it.qty or 0)
		rate = float(it.rate or 0)
		lines.append({
			"item_code":     it.item_code,
			"item_name":     it.item_name or it.item_code,
			"description":   it.description or "",
			"facility_name": it.get("facility_name") or "",
			"package_tier":  it.get("package_tier") or "",
			"qty":           qty,
			"rate":          rate,
			"amount":        float(it.amount or (qty * rate)),
		})

	net_total   = float(doc.net_total or sum(l["amount"] for l in lines))
	vat_amount  = float(doc.get("vat_amount") or round(net_total * VAT_RATE, 2))
	grand_total = float(doc.grand_total or round(net_total + vat_amount, 2))

	return {
		"name":          doc.name,
		"status":        _derive_status(doc),
		"editable":      int(doc.docstatus or 0) == 0,
		"currency":      doc.currency or "KES",
		"price_list":    doc.get("selling_price_list") or DEFAULT_PRICE_LIST,
		"payment_terms": doc.get("crm_payment_terms") or "Annual Upfront",
		"valid_until":   str(doc.valid_till or ""),
		"lines":         lines,
		"net_total":     round(net_total, 2),
		"vat_amount":    round(vat_amount, 2),
		"grand_total":   round(grand_total, 2),
	}


@frappe.whitelist()
def save_quote_lines(quote, lines):
	"""
	Persist exec-adjusted negotiated rates / quantities / added or removed lines
	on a Draft or Sent (docstatus=0) Quotation, then recompute totals.

	Requires Sales Manager or System Manager. This is the negotiated-rate control
	the exec uses before sending the contract — it sets QuotationItem.rate
	directly. A line submitted with no rate defaults to the quote price list's
	Item Price (ERPNext Item Price architecture).
	"""
	_require_manager()

	if isinstance(lines, str):
		lines = json.loads(lines)

	doc = frappe.get_doc("Quotation", quote)
	if int(doc.docstatus or 0) != 0:
		frappe.throw("Cannot edit a submitted or cancelled Quotation")

	price_list = doc.get("selling_price_list") or DEFAULT_PRICE_LIST

	new_items = []
	for row in (lines or []):
		item_code = frappe.utils.cstr(row.get("item_code") or "").strip()
		if not item_code:
			continue
		qty  = float(row.get("qty") or 0)
		if qty <= 0:
			continue
		# Distinguish "no rate supplied" (default from Item Price) from a deliberate
		# negotiated 0 (a waived / free line — a legitimate manual concession).
		raw_rate = row.get("rate")
		if raw_rate in (None, ""):
			rate = _get_item_price(item_code, price_list)
		else:
			rate = float(raw_rate)
		new_items.append({
			"item_code":     item_code,
			"item_name":     row.get("item_name") or item_code,
			"description":   row.get("description") or "",
			"qty":           qty,
			"rate":          rate,
			"uom":           _item_uom(item_code),
			"facility_name": row.get("facility_name") or "",
			"package_tier":  row.get("package_tier") or "",
		})

	if not new_items:
		frappe.throw("Quote must have at least one valid line item")

	doc.set("items", new_items)
	doc.flags.ignore_permissions = True  # SYSTEM-INTERNAL
	doc.flags.ignore_validate    = True
	doc.flags.ignore_mandatory   = True  # OIS quotes are created without a price list
	doc.set_missing_values()
	# Manual rates are authoritative — re-apply after set_missing_values so ERPNext
	# does not re-fetch price_list_rate over a negotiated (incl. waived 0) rate.
	_apply_manual_rates(doc, [it["rate"] for it in new_items])
	doc.calculate_taxes_and_totals()
	doc.vat_amount = round((doc.net_total or 0) * VAT_RATE, 2)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"name":        doc.name,
		"status":      _derive_status(doc),
		"net_total":   float(doc.net_total or 0),
		"vat_amount":  float(doc.vat_amount or 0),
		"grand_total": float(doc.grand_total or 0),
	}


@frappe.whitelist()
def list_catalogue_items(search=None, price_list=None):
	"""
	Catalogue for the inline quote 'add line' picker, sourced from ERPNext Items
	that carry a selling Item Price on the given (or default) price list. Each
	item's default rate comes from Item Price — the exec then negotiates it.
	Any sellable Item with a price is quotable, not just the 15 CRM Products.
	"""
	price_list = price_list or DEFAULT_PRICE_LIST

	item_filters = [["disabled", "=", 0], ["is_sales_item", "=", 1]]
	if search:
		item_filters.append(["item_name", "like", "%%%s%%" % search])

	items = frappe.get_list(
		"Item",
		filters=item_filters,
		fields=["name as item_code", "item_name", "stock_uom"],
		order_by="item_name asc",
		limit_page_length=100,
	)

	out = []
	for it in items:
		rate = _get_item_price(it.item_code, price_list)
		if not rate:
			continue  # only surface items that have a sellable price
		out.append({
			"item_code": it.item_code,
			"label":     it.item_name or it.item_code,
			"uom":       it.stock_uom or "Nos",
			"rate":      rate,
		})
	return out


@frappe.whitelist()
def check_quote_expiry():
	"""Daily scheduled job — notify deal owners of expired Draft/Sent Quotations."""
	expired = frappe.get_list(
		"Quotation",
		filters=[
			["docstatus", "=", 0],
			["valid_till", "<", nowdate()],
		],
		fields=["name", "crm_deal", "party_name as customer", "valid_till as valid_until"],
	)
	for q in expired:
		deal_owner = frappe.db.get_value("CRM Deal", q.crm_deal, "deal_owner") if q.crm_deal else None
		if not deal_owner:
			continue

		frappe.publish_realtime(
			"crm_notification",
			{
				"message": "Quotation %s has expired (valid until %s)" % (q.name, q.valid_until),
				"user": deal_owner,
			},
		)

		owner_email = frappe.db.get_value("User", deal_owner, "email")
		if owner_email:
			frappe.sendmail(
				recipients=[owner_email],
				subject="Quotation %s has expired" % q.name,
				message=(
					"Quotation %s for customer %s expired on %s. "
					"Please create a new version or follow up with the customer."
					% (q.name, q.customer, q.valid_until)
				),
				now=True,
			)
