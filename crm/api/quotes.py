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

Line items stored as QuotationItem rows:
  - Subscription row: item_code = CV-HIMS-SUB-*, facility_name, package_tier, rate = subscription_net
  - Implementation row: item_code = CV-HIMS-IMPL-*, facility_name, package_tier, rate = impl_net
  - Addon rows: item_code = CV-HW-*/CV-SW-*/CV-SVC-*, qty, rate = unit_price
"""
import json
import frappe
from frappe.utils import nowdate, add_days, getdate, date_diff

VAT_RATE         = 0.16
MONTHLY_SURCHARGE = 0.15
ANNUAL_TRUEUP    = 0.05

TIER_CAPS = {
	"No Partner": {"saas": 45.0, "services": 65.0},
	"Registered":  {"saas":  5.0, "services":  5.0},
	"Silver":      {"saas": 15.0, "services": 30.0},
	"Gold":        {"saas": 25.0, "services": 45.0},
	"Diamond":     {"saas": 45.0, "services": 65.0},
}

SKU_MAP = {
	("Core",       "subscription"): "CV-HIMS-SUB-CORE",
	("Advanced",   "subscription"): "CV-HIMS-SUB-ADV",
	("Enterprise", "subscription"): "CV-HIMS-SUB-ENT",
	("Core",       "impl"):         "CV-HIMS-IMPL-CORE",
	("Advanced",   "impl"):         "CV-HIMS-IMPL-ADV",
	("Enterprise", "impl"):         "CV-HIMS-IMPL-ENT",
}

_ADDON_CATEGORIES = {
	"CV-HW-":  "Hardware",
	"CV-SW-":  "Software",
	"CV-SVC-": "Professional Services",
}

# Frontend-facing status values derived from docstatus + crm_sent
_STATUS_ACCEPTED = "Accepted"
_STATUS_REJECTED = "Rejected"
_STATUS_SENT     = "Sent"
_STATUS_DRAFT    = "Draft"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _is_admin(roles):
	return "System Manager" in roles or frappe.session.user == "Administrator"


def _get_partner_tier(partner_name):
	if not partner_name:
		return "No Partner"
	partner_tier = frappe.db.get_value("CRM Partner", partner_name, "partner_tier") or "Registered"
	return partner_tier


def _get_caps(partner_name):
	tier = _get_partner_tier(partner_name)
	return TIER_CAPS.get(tier, TIER_CAPS["Registered"]), tier


def _sku_price(sku):
	row = frappe.get_list(
		"CRM Product",
		filters=[["product_code", "=", sku]],
		fields=["standard_rate", "max_discount"],
		limit=1,
	)
	if not row:
		frappe.throw("CRM Product not found: %s" % sku)
	return row[0].standard_rate or 0, row[0].max_discount or 0


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


def _addon_category(sku):
	for prefix, cat in _ADDON_CATEGORIES.items():
		if sku.startswith(prefix):
			return cat
	return "Professional Services"


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
	"""Create ERPNext Customer from CRM Deal organisation if not present."""
	if not customer_name or frappe.db.exists("Customer", customer_name):
		return customer_name or "Default Customer"
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
		existing = frappe.get_list("Customer", limit=1, pluck="name")
		customer_name = existing[0] if existing else customer_name
	return customer_name


def _compute_quote(quote_data, caps):
	"""
	Compute all derived pricing fields from raw quote_data dict.
	Returns updated quote_data with computed fields including renewal_schedule.
	Raises PermissionError if any discount exceeds the partner tier cap.
	"""
	facilities = quote_data.get("facilities") or []
	addons     = quote_data.get("addons") or []
	payment_terms    = quote_data.get("payment_terms") or "Annual Upfront"
	contract_term_yrs = int(quote_data.get("contract_term_yrs") or 1)
	max_saas     = caps["saas"]
	max_services = caps["services"]

	year1_subscription_total = 0.0
	year1_impl_total         = 0.0
	total_discount           = 0.0

	for row in facilities:
		tier     = row.get("package_tier")
		sub_sku  = SKU_MAP[(tier, "subscription")]
		impl_sku = SKU_MAP[(tier, "impl")]

		sub_list, _ = _sku_price(sub_sku)
		impl_list, _ = _sku_price(impl_sku)

		sub_disc  = float(row.get("subscription_discount") or 0)
		impl_disc = float(row.get("impl_discount") or 0)

		if sub_disc > max_saas:
			frappe.throw(
				"SaaS discount %s%% exceeds maximum allowed %s%% for this partner tier" % (sub_disc, max_saas),
				frappe.PermissionError,
			)
		if impl_disc > max_services:
			frappe.throw(
				"Services discount %s%% exceeds maximum allowed %s%% for this partner tier" % (impl_disc, max_services),
				frappe.PermissionError,
			)

		sub_net  = sub_list * (1 - sub_disc / 100)
		impl_net = impl_list * (1 - impl_disc / 100)

		if payment_terms == "Monthly":
			sub_net = sub_net * (1 + MONTHLY_SURCHARGE)

		row["subscription_sku"]        = sub_sku
		row["impl_sku"]                = impl_sku
		row["subscription_list_price"] = sub_list
		row["impl_list_price"]         = impl_list
		row["subscription_net"]        = round(sub_net, 2)
		row["impl_net"]                = round(impl_net, 2)
		row["facility_total"]          = round(sub_net + impl_net, 2)

		year1_subscription_total += sub_net
		year1_impl_total         += impl_net
		total_discount += (
			(sub_list - sub_list * (1 - sub_disc / 100))
			+ (impl_list - impl_list * (1 - impl_disc / 100))
		)

	addon_total = 0.0
	for row in addons:
		sku   = row.get("product_sku")
		price, _ = _sku_price(sku)
		qty   = float(row.get("qty") or 0)
		product_name = frappe.db.get_value("CRM Product", sku, "product_name") or sku
		row["description"] = product_name
		row["category"]    = _addon_category(sku)
		row["unit_price"]  = price
		row["total"]       = round(price * qty, 2)
		addon_total       += row["total"]

	subtotal    = round(year1_subscription_total + year1_impl_total + addon_total, 2)
	vat         = round(subtotal * VAT_RATE, 2)
	grand_total = round(subtotal + vat, 2)

	quote_data["subtotal_excl_vat"] = subtotal
	quote_data["discount_applied"]  = round(total_discount, 2)
	quote_data["vat_amount"]        = vat
	quote_data["grand_total"]       = grand_total

	# Build renewal schedule
	renewal  = []
	base_sub = year1_subscription_total
	if payment_terms == "Monthly":
		base_sub = base_sub / (1 + MONTHLY_SURCHARGE)

	for yr in range(1, contract_term_yrs + 1):
		sub_yr   = base_sub * ((1 + ANNUAL_TRUEUP) ** (yr - 1))
		impl_yr  = year1_impl_total if yr == 1 else 0.0
		addon_yr = addon_total if yr == 1 else 0.0
		gt_yr    = round((sub_yr + impl_yr + addon_yr) * (1 + VAT_RATE), 2)
		monthly_eq = round(gt_yr / 12, 2) if payment_terms == "Monthly" else 0.0
		renewal.append({
			"year": yr,
			"subscription_excl_vat": round(sub_yr, 2),
			"grand_total_incl_vat":  gt_yr,
			"monthly_equivalent":    monthly_eq,
		})

	quote_data["renewal_schedule"] = renewal
	return quote_data


def _build_items(computed):
	"""Build QuotationItem rows from computed facilities + addons."""
	items = []
	for row in (computed.get("facilities") or []):
		sub_item  = _resolve_item_code(row["subscription_sku"])
		impl_item = _resolve_item_code(row["impl_sku"])
		items.append({
			"item_code":     sub_item,
			"item_name":     "Careverse HMIS Subscription — %s (%s)" % (row["facility_name"], row["package_tier"]),
			"description":   "Careverse HMIS Subscription — %s" % row["facility_name"],
			"qty":           1,
			"rate":          row["subscription_net"],
			"uom":           _item_uom(sub_item),
			"facility_name": row.get("facility_name", ""),
			"package_tier":  row.get("package_tier", ""),
		})
		if (row.get("impl_net") or 0) > 0:
			items.append({
				"item_code":     impl_item,
				"item_name":     "Careverse HMIS Implementation & Training — %s" % row["facility_name"],
				"description":   "One-time implementation and training — %s" % row["facility_name"],
				"qty":           1,
				"rate":          row["impl_net"],
				"uom":           _item_uom(impl_item),
				"facility_name": row.get("facility_name", ""),
				"package_tier":  row.get("package_tier", ""),
			})
	for row in (computed.get("addons") or []):
		if (row.get("qty") or 0) > 0:
			addon_item = _resolve_item_code(row["product_sku"])
			items.append({
				"item_code":   addon_item,
				"item_name":   row.get("description") or addon_item,
				"description": row.get("description") or "",
				"qty":         row["qty"],
				"rate":        row["unit_price"],
				"uom":         _item_uom(addon_item),
			})
	return items


def _items_to_facilities_addons(items):
	"""
	Reconstruct {facilities, addons} from QuotationItem rows for the Vue frontend.
	Groups consecutive subscription+implementation rows by facility_name.
	"""
	facilities = {}
	addons = []
	facility_order = []

	for row in (items or []):
		fname = row.get("facility_name")
		tier  = row.get("package_tier")
		code  = row.get("item_code") or ""

		if fname and tier:
			if fname not in facilities:
				facilities[fname] = {
					"facility_name": fname,
					"package_tier": tier,
					"num_users": 0,
					"subscription_sku":    "",
					"impl_sku":            "",
					"subscription_net":    0.0,
					"impl_net":            0.0,
					"subscription_discount": 0.0,
					"impl_discount":         0.0,
				}
				facility_order.append(fname)
			fac = facilities[fname]
			if "SUB" in code:
				fac["subscription_sku"] = code
				fac["subscription_net"] = float(row.get("rate") or 0)
			elif "IMPL" in code:
				fac["impl_sku"] = code
				fac["impl_net"] = float(row.get("rate") or 0)
		else:
			# Addon row
			addons.append({
				"product_sku": code,
				"description": row.get("item_name") or "",
				"qty":         float(row.get("qty") or 0),
				"unit_price":  float(row.get("rate") or 0),
				"total":       float(row.get("qty") or 0) * float(row.get("rate") or 0),
				"category":    _addon_category(code),
			})

	return [facilities[n] for n in facility_order], addons


# ── Whitelisted API methods ────────────────────────────────────────────────────

@frappe.whitelist()
def get_quote_context(deal):
	"""Return partner tier, discount caps, customer name, and currency for the Quote Builder."""
	doc = frappe.get_doc("CRM Deal", deal)
	partner = None
	caps, tier = _get_caps(partner)

	partner_buy_saas = partner_buy_services = 0.0
	if partner:
		margin_map = {
			"Registered": (5.0,  5.0),
			"Silver":      (15.0, 30.0),
			"Gold":        (25.0, 45.0),
			"Diamond":     (40.0, 60.0),
		}
		partner_buy_saas, partner_buy_services = margin_map.get(tier, (0.0, 0.0))

	return {
		"partner_tier":           tier,
		"max_saas_discount":      caps["saas"],
		"max_services_discount":  caps["services"],
		"partner_buy_saas_pct":   partner_buy_saas,
		"partner_buy_services_pct": partner_buy_services,
		"customer": doc.get("organization") or "",
		"partner":  partner,
		"currency": "KES",
	}


@frappe.whitelist()
def save_quote(quote_data):
	"""Create or update an ERPNext Quotation from the Quote Builder payload."""
	if isinstance(quote_data, str):
		quote_data = json.loads(quote_data)

	deal = quote_data.get("deal")
	if not frappe.db.exists("CRM Deal", deal):
		frappe.throw("CRM Deal not found: %s" % deal)

	partner = quote_data.get("partner")
	caps, _ = _get_caps(partner)
	quote_data = _compute_quote(quote_data, caps)

	items = _build_items(quote_data)
	if not items:
		frappe.throw("Quote has no line items")

	customer_name = frappe.db.get_value("CRM Deal", deal, "organization") or ""
	customer_name = _ensure_customer(customer_name)

	prev = quote_data.get("previous_version")
	name = quote_data.get("name")

	# Cancel previous version if superseding
	if prev and frappe.db.exists("Quotation", prev):
		old = frappe.get_doc("Quotation", prev)
		if old.docstatus == 0:
			old.flags.ignore_permissions = True
			old.cancel()  # marks docstatus=2 → Rejected

	if name and frappe.db.exists("Quotation", name):
		doc = frappe.get_doc("Quotation", name)
		if doc.docstatus != 0:
			frappe.throw("Cannot edit a submitted or cancelled Quotation")

		doc.crm_payment_terms   = quote_data.get("payment_terms") or "Annual Upfront"
		doc.contract_term_yrs   = quote_data.get("contract_term_yrs") or 1
		doc.contract_start_date = quote_data.get("contract_start_date")
		doc.valid_till          = quote_data.get("valid_until") or add_days(nowdate(), 30)
		doc.currency            = quote_data.get("currency") or "KES"
		doc.terms               = quote_data.get("notes") or ""
		doc.discount_applied    = quote_data["discount_applied"]
		doc.vat_amount          = quote_data["vat_amount"]
		doc.set("items", items)
		doc.set("renewal_schedule", quote_data.get("renewal_schedule") or [])
		doc.flags.ignore_permissions = True  # SYSTEM-INTERNAL
		doc.flags.ignore_validate    = True
		doc.set_missing_values()
		doc.calculate_taxes_and_totals()
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		return {"name": doc.name, "status": _derive_status(doc)}

	# New Quotation
	doc = frappe.get_doc({
		"doctype": "Quotation",
		"quotation_to": "Customer",
		"party_name":   customer_name,
		"company":      frappe.db.get_single_value("Global Defaults", "default_company"),
		"transaction_date": quote_data.get("quote_date") or nowdate(),
		"valid_till":   quote_data.get("valid_until") or add_days(nowdate(), 30),
		"currency":     quote_data.get("currency") or "KES",
		"order_type":   "Sales",
		"crm_deal":     deal,
		"crm_partner":  partner,
		"crm_payment_terms":   quote_data.get("payment_terms") or "Annual Upfront",
		"contract_term_yrs":   quote_data.get("contract_term_yrs") or 1,
		"contract_start_date": quote_data.get("contract_start_date"),
		"previous_version":    prev,
		"discount_applied":    quote_data["discount_applied"],
		"vat_amount":          quote_data["vat_amount"],
		"terms":               quote_data.get("notes") or "",
		"items":               items,
		"renewal_schedule":    quote_data.get("renewal_schedule") or [],
	})
	doc.flags.ignore_permissions = True  # SYSTEM-INTERNAL
	doc.flags.ignore_validate    = True
	# Let ERPNext fill conversion_rate, price_list_currency, plc_conversion_rate etc.
	doc.set_missing_values()
	doc.calculate_taxes_and_totals()
	doc.insert(ignore_mandatory=True)
	frappe.db.commit()
	return {"name": doc.name, "status": _derive_status(doc)}


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
def get_quote_pdf_data(quote_name):
	"""
	Return Quotation data shaped like the old CRM Quote dict for the Vue frontend.
	Items are reconstructed into {facilities, addons} arrays.
	"""
	doc = frappe.get_doc("Quotation", quote_name)
	d = doc.as_dict()

	facilities, addons = _items_to_facilities_addons(
		[r.as_dict() if hasattr(r, "as_dict") else r for r in (doc.items or [])]
	)

	d["deal"]           = doc.get("crm_deal")
	d["customer"]       = doc.party_name
	d["partner"]        = doc.get("crm_partner")
	d["quote_date"]     = str(doc.transaction_date or "")
	d["valid_until"]    = str(doc.valid_till or "")
	d["payment_terms"]  = doc.get("crm_payment_terms") or "Annual Upfront"
	d["status"]         = _derive_status(doc)
	d["facilities"]     = facilities
	d["addons"]         = addons
	d["grand_total"]    = doc.grand_total
	d["vat_amount"]     = doc.get("vat_amount") or 0
	d["discount_applied"] = doc.get("discount_applied") or 0
	d["notes"]          = doc.terms or ""

	return d


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
			)
