# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Link-time Organization -> Lead/Deal enrichment copy.

The ONLY cross-record behaviour in Domain Enrichment: when a Lead or Deal links an
already-enriched ``CRM Organization``, synchronously copy that Organization's stored
enriched fields onto the *empty* fields of the Lead/Deal (fill-empty). The direction
is strictly Organization -> Lead/Deal, in-request, on the origin save. There is no
background job, no fan-out, and no write back to the Organization.

The actual field writing reuses :func:`crm.domain_enrichment.mapper.apply_to_document`
-- the single result->field authority -- by wrapping the Organization's stored values
in an :class:`~crm.domain_enrichment.result.EnrichmentResult`. No crawling happens
here; this is a pure record-to-record copy.
"""

from __future__ import annotations

import frappe

from crm.domain_enrichment import mapper
from crm.domain_enrichment.config import get_config
from crm.domain_enrichment.result import (
	EnrichmentResult,
	Field,
	SocialProfile,
)

# Native enriched fields stored on a CRM Organization. If at least one of these is
# populated (or the org has a completed enrichment run) we treat the org as enriched
# and worth copying from. Empty source values never overwrite anything (mapper guards).
_ORG_ENRICHED_FIELDS = (
	"company_description",
	"organization_logo",
	"industry",
	"linkedin",
	"twitter",
)


def _is_org_enriched(org) -> bool:
	"""Has this Organization actually been enriched?

	Cleanest signal: a completed ``CRM Enrichment Run`` for the org. We also accept
	any populated native enriched field as a fallback (an org may carry enriched data
	without a run row, e.g. seeded/imported data).
	"""
	if frappe.db.exists(
		"CRM Enrichment Run",
		{
			"reference_doctype": "CRM Organization",
			"reference_name": org.name,
			"status": "Completed",
		},
	):
		return True
	return any(org.get(fieldname) for fieldname in _ORG_ENRICHED_FIELDS)


def _result_from_organization(org) -> EnrichmentResult:
	"""Wrap an Organization's stored enriched fields in an EnrichmentResult so the
	shared mapper can copy them onto the target via the same Field Mapping records."""
	result = EnrichmentResult(website=org.get("website") or "")
	result.company_name = Field(value=org.get("organization_name") or "")
	result.description = Field(value=org.get("company_description") or "")
	result.logo = Field(value=org.get("organization_logo") or "")
	result.industry = Field(value=org.get("industry") or "")

	for network in ("linkedin", "twitter"):
		value = org.get(network)
		if value:
			result.social_profiles[network] = SocialProfile(value=value)

	return result


def copy_enrichment_from_organization(target_doc) -> list[str]:
	"""Copy enriched fields from the linked CRM Organization onto ``target_doc``.

	``target_doc`` is a CRM Lead or CRM Deal that has just linked an Organization
	(Lead: ``organization`` is free-text resolved to an org name; Deal: ``organization``
	is a Link to CRM Organization). If that Organization is actually enriched, its
	stored enriched fields are copied onto the *empty* fields of ``target_doc`` using
	the shared mapper with fill-empty semantics, so user-entered data is never touched.

	Best-effort: never raises, never blocks the Lead/Deal save. Returns the list of
	filled field labels (empty when nothing was copied).
	"""
	try:
		org_name = target_doc.get("organization")
		if not org_name or not frappe.db.exists("CRM Organization", org_name):
			return []

		org = frappe.get_cached_doc("CRM Organization", org_name)
		if not _is_org_enriched(org):
			return []

		cfg = get_config()
		result = _result_from_organization(org)
		# Fill-empty only: force fill-empty semantics for every mapping (even ones
		# configured "Always refresh") so the link-time copy never
		# overwrites or clears user-entered data. apply_to_document mutates target_doc
		# in place and does NOT save (the caller's save persists it).
		return mapper.apply_to_document(target_doc, result, cfg, fill_empty_only=True)
	except Exception:
		frappe.log_error(
			title="Domain Enrichment: Org -> Lead/Deal copy failed",
			message=f"{target_doc.doctype} {target_doc.name}: {frappe.get_traceback()}",
		)
		return []
