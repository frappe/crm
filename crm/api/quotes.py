import json
import frappe
from frappe.utils import nowdate, add_days, getdate, date_diff

VAT_RATE = 0.16
MONTHLY_SURCHARGE = 0.15
ANNUAL_TRUEUP = 0.05

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

# Categories for add-on SKU auto-classification
_ADDON_CATEGORIES = {
	"CV-HW-": "Hardware",
	"CV-SW-": "Software",
	"CV-SVC-": "Professional Services",
}


def _is_admin(roles):
	return "System Manager" in roles or frappe.session.user == "Administrator"


def _get_partner_tier(partner_name):
	if not partner_name:
		return "No Partner"
	tier = frappe.db.get_value("CRM Partner", partner_name, "partner_type") or "Registered"
	# partner_type on CRM Partner is "BD Partner" / "Technology Partner" — map to tier via rebate structure
	# Fall back: look for a partner_tier field if it exists, else use "Registered"
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


def _addon_category(sku):
	for prefix, cat in _ADDON_CATEGORIES.items():
		if sku.startswith(prefix):
			return cat
	return "Professional Services"


def _compute_quote(quote_data, caps):
	"""
	Compute all derived Currency fields from raw quote_data dict.
	Returns updated quote_data with computed fields.
	Raises frappe.PermissionError if any discount exceeds the cap.
	"""
	facilities = quote_data.get("facilities") or []
	addons = quote_data.get("addons") or []
	payment_terms = quote_data.get("payment_terms") or "Annual Upfront"
	contract_term_yrs = int(quote_data.get("contract_term_yrs") or 1)
	max_saas = caps["saas"]
	max_services = caps["services"]

	year1_subscription_total = 0.0
	year1_impl_total = 0.0
	total_discount = 0.0

	for row in facilities:
		tier = row.get("package_tier")
		sub_sku = SKU_MAP[(tier, "subscription")]
		impl_sku = SKU_MAP[(tier, "impl")]

		sub_list, _ = _sku_price(sub_sku)
		impl_list, _ = _sku_price(impl_sku)

		sub_disc = float(row.get("subscription_discount") or 0)
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

		sub_net = sub_list * (1 - sub_disc / 100)
		impl_net = impl_list * (1 - impl_disc / 100)

		# Monthly surcharge on subscription component
		if payment_terms == "Monthly":
			sub_net = sub_net * (1 + MONTHLY_SURCHARGE)

		row["subscription_sku"] = sub_sku
		row["impl_sku"] = impl_sku
		row["subscription_list_price"] = sub_list
		row["impl_list_price"] = impl_list
		row["subscription_net"] = round(sub_net, 2)
		row["impl_net"] = round(impl_net, 2)
		row["facility_total"] = round(sub_net + impl_net, 2)

		year1_subscription_total += sub_net
		year1_impl_total += impl_net
		total_discount += (sub_list - (sub_list * (1 - sub_disc / 100))) + (impl_list - (impl_list * (1 - impl_disc / 100)))

	addon_total = 0.0
	for row in addons:
		sku = row.get("product_sku")
		price, _ = _sku_price(sku)
		qty = float(row.get("qty") or 0)
		product_name = frappe.db.get_value("CRM Product", sku, "product_name") or sku
		row["description"] = product_name
		row["category"] = _addon_category(sku)
		row["unit_price"] = price
		row["total"] = round(price * qty, 2)
		addon_total += row["total"]

	subtotal = round(year1_subscription_total + year1_impl_total + addon_total, 2)
	vat = round(subtotal * VAT_RATE, 2)
	grand_total = round(subtotal + vat, 2)

	quote_data["subtotal_excl_vat"] = subtotal
	quote_data["discount_applied"] = round(total_discount, 2)
	quote_data["vat_amount"] = vat
	quote_data["grand_total"] = grand_total

	# Build renewal schedule
	renewal = []
	base_sub = year1_subscription_total
	# Remove monthly surcharge from base for renewal calculation (renewal is always annual billing base)
	if payment_terms == "Monthly":
		base_sub = base_sub / (1 + MONTHLY_SURCHARGE)

	for yr in range(1, contract_term_yrs + 1):
		sub_yr = base_sub * ((1 + ANNUAL_TRUEUP) ** (yr - 1))
		impl_yr = year1_impl_total if yr == 1 else 0.0
		addon_yr = addon_total if yr == 1 else 0.0
		gt_yr = round((sub_yr + impl_yr + addon_yr) * (1 + VAT_RATE), 2)
		monthly_eq = round(gt_yr / 12, 2) if payment_terms == "Monthly" else 0.0
		renewal.append({
			"year": yr,
			"subscription_excl_vat": round(sub_yr, 2),
			"grand_total_incl_vat": gt_yr,
			"monthly_equivalent": monthly_eq,
		})

	quote_data["renewal_schedule"] = renewal
	return quote_data


@frappe.whitelist()
def get_quote_context(deal):
	doc = frappe.get_doc("CRM Deal", deal)
	# CRM Deal in this fork has no partner field — partner comes from the quote itself
	partner = None
	caps, tier = _get_caps(partner)

	# Partner buy-price margins
	partner_buy_saas = 0.0
	partner_buy_services = 0.0
	if partner:
		margin_map = {
			"Registered": (5.0,  5.0),
			"Silver":      (15.0, 30.0),
			"Gold":        (25.0, 45.0),
			"Diamond":     (40.0, 60.0),
		}
		partner_buy_saas, partner_buy_services = margin_map.get(tier, (0.0, 0.0))

	return {
		"partner_tier": tier,
		"max_saas_discount": caps["saas"],
		"max_services_discount": caps["services"],
		"partner_buy_saas_pct": partner_buy_saas,
		"partner_buy_services_pct": partner_buy_services,
		"customer": doc.get("organization") or "",
		"partner": partner,
		"currency": "KES",
	}


@frappe.whitelist()
def save_quote(quote_data):
	if isinstance(quote_data, str):
		quote_data = json.loads(quote_data)

	deal = quote_data.get("deal")
	if not frappe.db.exists("CRM Deal", deal):
		frappe.throw("CRM Deal not found: %s" % deal)

	# Resolve partner and caps
	# Partner comes from the quote data (not CRM Deal, which has no partner field in this fork)
	partner = quote_data.get("partner")
	caps, _ = _get_caps(partner)

	# Compute all derived fields
	quote_data = _compute_quote(quote_data, caps)

	# Handle previous_version: if provided, set old quote to Rejected
	prev = quote_data.get("previous_version")
	if prev and frappe.db.exists("CRM Quote", prev):
		frappe.db.set_value("CRM Quote", prev, "status", "Rejected")

	name = quote_data.get("name")
	if name and frappe.db.exists("CRM Quote", name):
		# Update existing quote
		doc = frappe.get_doc("CRM Quote", name)
		if doc.status in ("Accepted", "Rejected"):
			frappe.throw("Cannot edit a quote in %s status" % doc.status)
		# Update header fields
		update_fields = [
			"payment_terms", "contract_term_yrs", "currency", "notes", "terms_and_conditions",
			"valid_until", "contract_start_date", "quote_date",
			"subtotal_excl_vat", "discount_applied", "vat_amount", "grand_total",
		]
		for f in update_fields:
			if f in quote_data:
				doc.set(f, quote_data[f])
		doc.set("facilities", quote_data.get("facilities") or [])
		doc.set("addons", quote_data.get("addons") or [])
		doc.set("renewal_schedule", quote_data.get("renewal_schedule") or [])
		doc.save(ignore_permissions=True)  # SYSTEM-INTERNAL
		return {"name": doc.name, "status": doc.status}
	else:
		# Insert new quote
		doc = frappe.get_doc({
			"doctype": "CRM Quote",
			"deal": deal,
			"customer": frappe.db.get_value('CRM Deal', deal, 'organization') or '',
			"partner": partner,
			"quote_date": quote_data.get("quote_date") or nowdate(),
			"valid_until": quote_data.get("valid_until") or add_days(nowdate(), 30),
			"contract_start_date": quote_data.get("contract_start_date"),
			"payment_terms": quote_data.get("payment_terms") or "Annual Upfront",
			"contract_term_yrs": quote_data.get("contract_term_yrs") or 1,
			"currency": quote_data.get("currency") or "KES",
			"previous_version": prev,
			"notes": quote_data.get("notes"),
			"terms_and_conditions": quote_data.get("terms_and_conditions"),
			"subtotal_excl_vat": quote_data["subtotal_excl_vat"],
			"discount_applied": quote_data["discount_applied"],
			"vat_amount": quote_data["vat_amount"],
			"grand_total": quote_data["grand_total"],
			"facilities": quote_data.get("facilities") or [],
			"addons": quote_data.get("addons") or [],
			"renewal_schedule": quote_data.get("renewal_schedule") or [],
		})
		doc.insert(ignore_permissions=True)  # SYSTEM-INTERNAL
		frappe.db.commit()
		return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def list_quotes(deal):
	return frappe.get_list(
		"CRM Quote",
		filters=[["deal", "=", deal]],
		fields=[
			"name", "quote_date", "valid_until", "contract_start_date",
			"grand_total", "status", "payment_terms", "contract_term_yrs",
			"erpnext_sales_invoice", "previous_version", "currency", "creation",
		],
		order_by="creation desc",
	)


@frappe.whitelist()
def list_all_quotes(status=None, from_date=None, to_date=None, search=None, page=0, page_size=20):
	roles = frappe.get_roles(frappe.session.user)
	user = frappe.session.user
	filters = []

	if not (_is_admin(roles) or "Finance Manager" in roles or "Accounts Manager" in roles):
		if "Sales Manager" in roles:
			# Team deals: deals where owner is in user's team — for now scope to all deals the user can see
			# Full team hierarchy is a future enhancement; for now Sales Manager sees own + subordinates
			team_users = frappe.get_list(
				"User", filters=[["name", "!=", "Administrator"]], pluck="name", limit=500
			)
			team_deals = frappe.get_list(
				"CRM Deal",
				filters=[["deal_owner", "in", team_users]],
				pluck="name",
				limit=2000,
			) or ["__none__"]
			filters.append(["deal", "in", team_deals])
		elif "Partner RM" in roles:
			own_partners = frappe.get_list(
				"CRM Partner", filters={"partner_rm": user}, pluck="name"
			) or ["__none__"]
			partner_deals = frappe.get_list(
				"CRM Deal",
				filters=[["partner", "in", own_partners]],
				pluck="name",
				limit=2000,
			) or ["__none__"]
			filters.append(["deal", "in", partner_deals])
		else:
			# Sales User: own quotes only
			own_deals = frappe.get_list(
				"CRM Deal", filters={"deal_owner": user}, pluck="name"
			) or ["__none__"]
			filters.append(["deal", "in", own_deals])

	if status and status not in ("All", "Expired"):
		filters.append(["status", "=", status])
	elif status == "Expired":
		filters.append(["valid_until", "<", nowdate()])
		filters.append(["status", "in", ["Draft", "Sent"]])

	if from_date:
		filters.append(["quote_date", ">=", from_date])
	if to_date:
		filters.append(["quote_date", "<=", to_date])
	if search:
		filters.append(["name", "like", "%%%s%%" % search])

	rows = frappe.get_list(
		"CRM Quote",
		filters=filters,
		fields=[
			"name", "deal", "customer", "partner", "quote_date", "valid_until",
			"grand_total", "status", "payment_terms", "contract_term_yrs",
			"submitted_by as owner", "creation", "erpnext_sales_invoice",
		],
		order_by="quote_date desc",
		limit_page_length=int(page_size),
		limit_start=int(page) * int(page_size),
	)

	total = frappe.db.count("CRM Quote", filters)
	kpis = _quote_kpis(roles)

	return {"rows": rows, "total": total, "kpis": kpis}


def _quote_kpis(roles):
	try:
		draft_count = frappe.db.count("CRM Quote", {"status": "Draft"})
		sent_count  = frappe.db.count("CRM Quote", {"status": "Sent"})

		# Accepted this month
		from frappe.utils import get_first_day
		month_start = get_first_day(nowdate())
		accepted_rows = frappe.get_list(
			"CRM Quote",
			filters=[["status", "=", "Accepted"], ["quote_date", ">=", month_start]],
			fields=[{"SUM": "grand_total", "as": "total"}],
			limit=1,
		)
		accepted_value = float((accepted_rows[0].total or 0) if accepted_rows else 0)

		# Pipeline value
		pipeline_rows = frappe.get_list(
			"CRM Quote",
			filters=[["status", "in", ["Draft", "Sent"]]],
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
	doc = frappe.get_doc("CRM Quote", quote_name)
	if doc.status not in ("Draft", "Sent"):
		frappe.throw("Can only send a Draft or Sent quote")

	# Get rep's full name for from_name
	rep_name = frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user

	# Get primary contact email from deal
	deal = frappe.get_doc("CRM Deal", doc.deal)
	recipient_email = None
	for c in (deal.contacts or []):
		if c.is_primary:
			recipient_email = frappe.db.get_value("Contact", c.contact, "email_id")
			break
	if not recipient_email:
		recipient_email = frappe.db.get_value("Customer", doc.customer, "customer_primary_email") or ""

	# Generate PDF
	pdf_data = frappe.get_print("CRM Quote", quote_name, "CRM Quote Standard", as_pdf=True)

	if recipient_email:
		frappe.sendmail(
			recipients=[recipient_email],
			subject="Quotation %s — Tiberbu CareVerse HIMS" % quote_name,
			message="Please find attached the quotation %s from Tiberbu Healthnet Solutions." % quote_name,
			attachments=[{"fname": "%s.pdf" % quote_name, "fcontent": pdf_data}],
			sender=frappe.db.get_single_value("Email Account", "email_id") or "sales@tiberbu.com",
			sender_full_name=rep_name,
		)

	doc.db_set("status", "Sent")
	doc.db_set("submitted_by", frappe.session.user)
	frappe.db.commit()

	return {"status": "sent", "quote_name": quote_name, "sent_to": recipient_email or ""}


@frappe.whitelist()
def accept_quote(quote_name):
	doc = frappe.get_doc("CRM Quote", quote_name)
	if doc.status != "Sent":
		frappe.throw("Only Sent quotes can be accepted")

	from crm.integrations.erpnext.invoice_adapter import create_sales_invoice
	result = create_sales_invoice(doc)
	invoice_name = result.get("invoice_name", "")

	doc.db_set("status", "Accepted")
	if invoice_name:
		doc.db_set("erpnext_sales_invoice", invoice_name)
	frappe.db.commit()

	return {"status": "accepted", "quote_name": quote_name, "invoice_name": invoice_name}


@frappe.whitelist()
def reject_quote(quote_name):
	doc = frappe.get_doc("CRM Quote", quote_name)
	if doc.status == "Accepted":
		frappe.throw("Accepted quotes cannot be rejected")
	doc.db_set("status", "Rejected")
	frappe.db.commit()
	return {"status": "rejected", "quote_name": quote_name}


@frappe.whitelist()
def get_quote_pdf_data(quote_name):
	doc = frappe.get_doc("CRM Quote", quote_name)
	return doc.as_dict()


@frappe.whitelist()
def check_quote_expiry():
	"""Daily scheduled job — notify deal owners of expired Draft/Sent quotes."""
	expired = frappe.get_list(
		"CRM Quote",
		filters=[
			["status", "in", ["Draft", "Sent"]],
			["valid_until", "<", nowdate()],
		],
		fields=["name", "deal", "customer", "valid_until", "submitted_by"],
	)
	for q in expired:
		deal_owner = frappe.db.get_value("CRM Deal", q.deal, "deal_owner") if q.deal else None
		if not deal_owner:
			continue

		# In-app notification
		frappe.publish_realtime(
			"crm_notification",
			{
				"message": "Quote %s has expired (valid until %s)" % (q.name, q.valid_until),
				"user": deal_owner,
			},
		)

		# Email notification
		owner_email = frappe.db.get_value("User", deal_owner, "email")
		if owner_email:
			frappe.sendmail(
				recipients=[owner_email],
				subject="CRM Quote %s has expired" % q.name,
				message=(
					"Quote %s for customer %s expired on %s. "
					"Please create a new version or follow up with the customer."
					% (q.name, q.customer, q.valid_until)
				),
			)
