# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""One-time code-to-data migration of the enrichment knowledge base.

The POC baked its keyword / signature / mapping tables into Python constants.
This seeder translates them into editable desk records (CRM Enrichment Rule +
Pattern, CRM Enrichment Field Mapping) so a sales-ops admin owns the knowledge.

Everything here is idempotent (skip-if-exists) and wired into both ``after_install``
and ``after_migrate`` so a fresh install and every migrate land the defaults
without clobbering admin edits.
"""

import frappe

# --------------------------------------------------------------------------- #
# Rule knowledge (recovered from the POC's extractors.py constant tables)
# --------------------------------------------------------------------------- #

# industry -> keywords (matched against headline text, weight 1 each)
INDUSTRY_KEYWORDS = {
	"ERP": [
		"erp",
		"enterprise resource planning",
		"procurement",
		"supply chain management",
		"inventory management",
	],
	"CRM": [
		"crm",
		"customer relationship management",
		"sales pipeline",
		"lead management",
		"contact management",
	],
	"Ecommerce": [
		"ecommerce",
		"e-commerce",
		"online shopping",
		"online store",
		"marketplace",
		"shopping cart",
		"add to cart",
		"add to bag",
		"storefront",
		"checkout",
		"shop",
		"free shipping",
		"free returns",
		"new arrivals",
		"best sellers",
		"bestsellers",
		"size guide",
		"apparel",
		"clothing brand",
		"direct-to-consumer",
		"quick commerce",
		"q-commerce",
		"online grocery",
		"online groceries",
		"grocery delivery",
		"grocery app",
		"delivery app",
		"online shop",
	],
	"SaaS": ["saas", "software as a service", "subscription software", "cloud platform", "free trial"],
	"Technology": [
		"software",
		"developer",
		"developers",
		"api",
		"open source",
		"cloud computing",
		"it services",
		"information technology",
		"artificial intelligence",
		"machine learning",
	],
	"Semiconductors": [
		"semiconductor",
		"gpu",
		"graphics card",
		"processor",
		"chipset",
		"supercomputer",
		"microprocessor",
	],
	"Manufacturing": [
		"manufacturing",
		"factory",
		"production line",
		"assembly line",
		"fabrication",
		"industrial equipment",
		"3d printing",
		"additive manufacturing",
		"cnc machining",
		"rapid prototyping",
		"injection molding",
		"prototyping",
	],
	"Healthcare": [
		"healthcare",
		"health care",
		"clinic",
		"hospital",
		"patient care",
		"medical",
		"telehealth",
		"pharmaceutical",
		"pharma",
	],
	"Education": [
		"education",
		"e-learning",
		"students",
		"curriculum",
		"university",
		"online courses",
		"courses",
		"course",
		"edtech",
		"learning platform",
	],
	"Consulting": [
		"consulting",
		"advisory services",
		"consultants",
		"professional services",
		"strategy consulting",
	],
	"Marketing": [
		"marketing agency",
		"digital marketing",
		"advertising agency",
		"seo services",
		"ad campaigns",
		"media buying",
	],
	"Finance": [
		"fintech",
		"banking",
		"payments",
		"lending",
		"insurance",
		"financial services",
		"trading",
		"wealth management",
	],
	"Logistics": [
		"logistics",
		"freight",
		"warehousing",
		"fulfillment",
		"shipping carrier",
		"last-mile delivery",
	],
	"Food & Beverage": [
		"food and beverage",
		"beverage",
		"beverages",
		"snacks",
		"snack",
		"packaged food",
		"fmcg",
		"consumer goods",
		"sparkling water",
		"iced tea",
		"energy drink",
		"soft drink",
		"drink",
		"drinks",
		"soda",
		"kombucha",
		"cereal",
		"coffee",
		"chocolate",
		"protein bar",
	],
	"Retail": ["retailer", "department store", "brick and mortar"],
	"Media": [
		"entertainment",
		"streaming service",
		"video game",
		"game studio",
		"publishing house",
		"news media",
		"broadcasting",
		"journalism",
		"journalists",
		"media company",
		"newsroom",
		"newsletter",
		"reported articles",
		"investigative",
		"editorial",
		"magazine",
		"podcast",
		"reporting on",
	],
	"Real Estate": [
		"real estate",
		"property management",
		"commercial property",
		"interior design",
		"home design",
		"home improvement",
		"remodeling",
		"decorating",
		"home renovation",
	],
	"Travel": ["hospitality", "tourism", "flight booking", "travel agency"],
	"Automotive": ["automotive", "electric vehicle", "car manufacturer"],
	"Telecom": ["telecommunications", "broadband", "network operator"],
	"Energy": ["renewable energy", "solar power", "oil and gas"],
	"Legal": [
		"law firm",
		"legal services",
		"litigation",
		"legal help",
		"legal documents",
		"legal advice",
		"attorney",
		"attorneys",
		"lawyer",
		"lawyers",
	],
	"Nonprofit": ["nonprofit", "non-profit", "ngo", "charity"],
}

# social network -> regex (matched against HTML; stored as regex patterns)
SOCIAL_PATTERNS = {
	"linkedin": [r"linkedin\.com/(company|in|school)/"],
	"twitter": [r"(twitter\.com|x\.com)/[A-Za-z0-9_]+"],
	"github": [r"github\.com/[A-Za-z0-9_.-]+"],
	"facebook": [r"facebook\.com/[A-Za-z0-9_.\-/]+"],
	"instagram": [r"instagram\.com/[A-Za-z0-9_.]+"],
	"youtube": [r"youtube\.com/(channel/|c/|user/|@)[A-Za-z0-9_.\-]+"],
}

# --------------------------------------------------------------------------- #
# Field-mapping knowledge (recovered from the POC's api/website_intelligence.py)
# Translates FIELD_MAP / OVERRIDABLE_DEFAULTS / ALWAYS_REFRESH into records.
# (source_key, target_doctype, target_fieldname, write_policy, default_values, create_missing_link)
# --------------------------------------------------------------------------- #
_LEAD = "CRM Lead"
_DEAL = "CRM Deal"
_ORG = "CRM Organization"

# Per-doctype the org "name" lands on a different field: Lead.organization,
# Deal.organization_name (free text), Org.organization_name.
FIELD_MAPPINGS = [
	# company name
	("company_name", _LEAD, "organization", "Fill if empty", None, 0),
	("company_name", _DEAL, "organization_name", "Fill if empty", None, 0),
	("company_name", _ORG, "organization_name", "Fill if empty", None, 0),
	# logo / description (shared)
	*[
		(k, dt, fn, "Fill if empty", None, 0)
		for dt in (_LEAD, _DEAL, _ORG)
		for k, fn in (("logo", "organization_logo"), ("description", "company_description"))
	],
	# industry — link, opt-in auto-create of missing CRM Industry
	*[("industry", dt, "industry", "Fill if empty", None, 1) for dt in (_LEAD, _DEAL, _ORG)],
	# social links (shared, fill-empty)
	*[
		(k, dt, fn, "Fill if empty", None, 0)
		for dt in (_LEAD, _DEAL, _ORG)
		for k, fn in (("linkedin", "linkedin"), ("twitter", "twitter"))
	],
]


def seed_default_rules_and_mappings():
	"""Idempotently create the default enrichment rules + field mappings.

	Safe to run repeatedly (after_install + after_migrate): each record is keyed
	on a stable name and skipped if it already exists, so admin edits are never
	clobbered.
	"""
	_seed_industry_rules()
	_seed_social_rules()
	_seed_field_mappings()


def _ensure_industry(industry: str):
	if not frappe.db.exists("CRM Industry", industry):
		frappe.get_doc({"doctype": "CRM Industry", "industry": industry}).insert(ignore_permissions=True)


def _make_rule(
	rule_name,
	rule_type,
	patterns,
	*,
	target_value=None,
	industry=None,
	weight=1,
	match_scope="Full Text",
	is_regex=False,
):
	if frappe.db.exists("CRM Enrichment Rule", rule_name):
		return
	doc = frappe.get_doc(
		{
			"doctype": "CRM Enrichment Rule",
			"rule_name": rule_name,
			"rule_type": rule_type,
			"target_value": target_value,
			"industry": industry,
			"weight": weight,
			"match_scope": match_scope,
			"enabled": 1,
			"patterns": [{"pattern": p, "is_regex": 1 if is_regex else 0} for p in patterns],
		}
	)
	doc.insert(ignore_permissions=True)


def _seed_industry_rules():
	for industry, keywords in INDUSTRY_KEYWORDS.items():
		_ensure_industry(industry)
		_make_rule(
			f"Industry: {industry}",
			"Industry",
			keywords,
			industry=industry,
			match_scope="Headline",
		)


def _seed_social_rules():
	for network, patterns in SOCIAL_PATTERNS.items():
		_make_rule(
			f"Social: {network}",
			"Social",
			patterns,
			target_value=network,
			match_scope="HTML",
			is_regex=True,
		)


def _seed_field_mappings():
	for (
		source_key,
		target_doctype,
		target_fieldname,
		write_policy,
		default_values,
		create_link,
	) in FIELD_MAPPINGS:
		exists = frappe.db.exists(
			"CRM Enrichment Field Mapping",
			{
				"source_key": source_key,
				"target_doctype": target_doctype,
				"target_fieldname": target_fieldname,
			},
		)
		if exists:
			continue
		frappe.get_doc(
			{
				"doctype": "CRM Enrichment Field Mapping",
				"enabled": 1,
				"source_key": source_key,
				"target_doctype": target_doctype,
				"target_fieldname": target_fieldname,
				"write_policy": write_policy,
				"default_values": default_values,
				"create_missing_link": create_link,
			}
		).insert(ignore_permissions=True)
