# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Idempotent seeding of the Registry Enrichment defaults.

Two things land here, both skip-if-exists so a fresh install and every migrate apply
them without clobbering admin edits: the Brazilian fiscal Custom Fields on CRM
Organization / CRM Lead (via ``create_custom_fields``, which updates in place rather
than duplicating), and the default field-mapping rows embedded in the Settings Single.
Wired into both ``after_install`` and ``after_migrate``.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

_ORG = "CRM Organization"
_LEAD = "CRM Lead"

# Registration-status Select options (English), matching the normalizer's status map.
_STATUS_OPTIONS = "\nActive\nSuspended\nUnfit\nClosed\nNull"

# Custom Fields per target doctype. Organization carries the full fiscal set; Lead gets
# the qualification-relevant subset (Lead has no native Address, share_capital, etc.).
CUSTOM_FIELDS = {
	_ORG: [
		{"fieldname": "tax_id", "label": "Tax ID", "fieldtype": "Data", "insert_after": "website"},
		{"fieldname": "trade_name", "label": "Trade Name", "fieldtype": "Data", "insert_after": "tax_id"},
		{
			"fieldname": "registration_status",
			"label": "Registration Status",
			"fieldtype": "Select",
			"options": _STATUS_OPTIONS,
			"insert_after": "trade_name",
		},
		{
			"fieldname": "registration_status_date",
			"label": "Registration Status Date",
			"fieldtype": "Date",
			"insert_after": "registration_status",
		},
		{
			"fieldname": "opening_date",
			"label": "Opening Date",
			"fieldtype": "Date",
			"insert_after": "registration_status_date",
		},
		{
			"fieldname": "legal_nature",
			"label": "Legal Nature",
			"fieldtype": "Data",
			"insert_after": "opening_date",
		},
		{
			"fieldname": "company_size",
			"label": "Company Size",
			"fieldtype": "Data",
			"insert_after": "legal_nature",
		},
		{
			"fieldname": "share_capital",
			"label": "Share Capital",
			"fieldtype": "Currency",
			"insert_after": "company_size",
		},
		{
			"fieldname": "tax_regime",
			"label": "Tax Regime",
			"fieldtype": "Data",
			"insert_after": "share_capital",
		},
		{
			"fieldname": "simples_nacional",
			"label": "Simples Nacional",
			"fieldtype": "Check",
			"default": "0",
			"insert_after": "tax_regime",
		},
	],
	_LEAD: [
		{"fieldname": "tax_id", "label": "Tax ID", "fieldtype": "Data", "insert_after": "website"},
		{"fieldname": "trade_name", "label": "Trade Name", "fieldtype": "Data", "insert_after": "tax_id"},
		{
			"fieldname": "registration_status",
			"label": "Registration Status",
			"fieldtype": "Select",
			"options": _STATUS_OPTIONS,
			"insert_after": "trade_name",
		},
		{
			"fieldname": "opening_date",
			"label": "Opening Date",
			"fieldtype": "Date",
			"insert_after": "registration_status",
		},
		{
			"fieldname": "company_size",
			"label": "Company Size",
			"fieldtype": "Data",
			"insert_after": "opening_date",
		},
	],
}

# Default mappings: (source_key, target_doctype, target_fieldname, write_policy, create_missing_link).
# Every default is "Fill if empty" so enrichment never overwrites user-entered data, with
# one deliberate exception: ``tax_id`` is seeded "Always refresh" so the stored CNPJ is
# rewritten to its canonical normalized form (digits/upper-case alphanumeric only) even
# when the user typed a formatted value -- the registry lookup keys on the same
# normalized document, so storing it canonically keeps the field consistent with what
# was queried. "Always refresh" never clears a value to empty, so this cannot erase data.
FIELD_MAPPINGS = [
	# Organization
	("legal_name", _ORG, "organization_name", "Fill if empty", 0),
	("trade_name", _ORG, "trade_name", "Fill if empty", 0),
	("tax_id", _ORG, "tax_id", "Always refresh", 0),
	("registration_status", _ORG, "registration_status", "Fill if empty", 0),
	("registration_status_date", _ORG, "registration_status_date", "Fill if empty", 0),
	("opening_date", _ORG, "opening_date", "Fill if empty", 0),
	("legal_nature", _ORG, "legal_nature", "Fill if empty", 0),
	("company_size", _ORG, "company_size", "Fill if empty", 0),
	("share_capital", _ORG, "share_capital", "Fill if empty", 0),
	("tax_regime", _ORG, "tax_regime", "Fill if empty", 0),
	("simples_nacional", _ORG, "simples_nacional", "Fill if empty", 0),
	("industry_section", _ORG, "industry", "Fill if empty", 1),
	("address", _ORG, "address", "Fill if empty", 0),
	# Lead
	("legal_name", _LEAD, "organization", "Fill if empty", 0),
	("trade_name", _LEAD, "trade_name", "Fill if empty", 0),
	("tax_id", _LEAD, "tax_id", "Always refresh", 0),
	("registration_status", _LEAD, "registration_status", "Fill if empty", 0),
	("opening_date", _LEAD, "opening_date", "Fill if empty", 0),
	("company_size", _LEAD, "company_size", "Fill if empty", 0),
	("industry_section", _LEAD, "industry", "Fill if empty", 1),
	("email", _LEAD, "email", "Fill if empty", 0),
	("phone", _LEAD, "phone", "Fill if empty", 0),
	("mobile_no", _LEAD, "mobile_no", "Fill if empty", 0),
]


def create_registry_custom_fields():
	"""Idempotently create the Brazilian fiscal Custom Fields on CRM Organization / Lead.

	Extracted from ``seed_defaults`` so the layout patch can guarantee the fields exist
	before it places them on a form layout. ``create_custom_fields`` updates in place
	rather than duplicating, so calling this repeatedly is safe.
	"""
	create_custom_fields(CUSTOM_FIELDS, ignore_validate=True)


def seed_defaults():
	"""Idempotently create the fiscal Custom Fields and the default field mappings.

	Safe to run repeatedly (after_install + after_migrate): Custom Fields are updated
	in place and mapping rows are keyed on (source_key, target_doctype,
	target_fieldname) and skipped if already present, so admin edits are never lost.
	"""
	create_registry_custom_fields()
	_seed_field_mappings()


def _seed_field_mappings():
	settings = frappe.get_single("CRM Registry Enrichment Settings")
	existing = {
		(row.source_key, row.target_doctype, row.target_fieldname) for row in settings.field_mappings or []
	}
	added = False
	for source_key, target_doctype, target_fieldname, write_policy, create_link in FIELD_MAPPINGS:
		if (source_key, target_doctype, target_fieldname) in existing:
			continue
		settings.append(
			"field_mappings",
			{
				"enabled": 1,
				"source_key": source_key,
				"target_doctype": target_doctype,
				"target_fieldname": target_fieldname,
				"write_policy": write_policy,
				"create_missing_link": create_link,
			},
		)
		added = True
	if added:
		settings.save(ignore_permissions=True)
