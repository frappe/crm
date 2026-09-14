# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Domain Enrichment engine.

Config-driven, Frappe-idiomatic feature that enriches CRM Lead/Deal/Organization
records from their website domain. Configuration (rules, field mappings, crawl
limits, sources) lives in desk doctypes; this package is the rule-agnostic engine.
"""
