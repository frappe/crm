# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Registry Enrichment engine (CPF.CNPJ).

Config-driven, Frappe-idiomatic feature that enriches CRM Lead/Organization records
from a Brazilian tax id (CNPJ) via the public CPF.CNPJ registry API. It mirrors the
shape of the ``domain_enrichment`` module (Settings + Field Mappings + Run history,
a background worker, whitelisted entry points and an auto-enrich-on-create trigger)
and reuses its write-policy mechanics, so a maintainer familiar with one reads the
other. Phase 1 covers Organization and Lead lookups by CNPJ (package 6): no QSA
partners, no state registration, no CPF.
"""
