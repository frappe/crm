# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Whitelisted entry points: ``enrich`` (enqueue a full run for a record) and
``retry`` (re-run one from its Run history).

Both are type-annotated -- hooks.py sets ``require_type_annotated_api_methods``.
Security: each enforces the doctype allow-list (from Settings) + a ``write``
permission check, and is rate-limited per user (see ``ENRICH_RATE_LIMIT``).
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit

from .config import ENRICHABLE_DOCTYPES, EnrichmentConfig, get_config
from .tasks import enqueue_enrichment

# Per-user, per-minute cap on each enrich entry point (each gets its own bucket).
# Both only enqueue a per-doc-deduplicated job -- 10/min is far above any real human
# burst while capping scripted queue-flooding.
ENRICH_RATE_LIMIT = 10


def _enabled_doctypes(cfg: EnrichmentConfig) -> list[str]:
	"""The doctypes enrichment is enabled for, per Settings (allow-list)."""
	if not cfg.setting("enabled"):
		return []
	return list(ENRICHABLE_DOCTYPES)


def _enqueue_run(cfg, reference_doctype: str, reference_name: str, website: str) -> dict:
	"""Validate + enqueue one enrichment run for a target record. Shared by
	``enrich`` (initial trigger from the record) and ``retry`` (re-run from a Run).

	Caller must have already resolved the website. Enforces the Settings allow-list
	and ``write`` permission on the target. Uses the per-doc ``job_id`` +
	``deduplicate`` so a second trigger while one is in-flight is a no-op.
	"""
	if reference_doctype not in _enabled_doctypes(cfg):
		frappe.throw(
			_("Enrichment is not enabled for {0}.").format(reference_doctype),
			frappe.ValidationError,
		)

	doc = frappe.get_doc(reference_doctype, reference_name)
	doc.check_permission("write")

	website = (website or "").strip()
	if not website:
		frappe.throw(_("Set a website on this record before enriching."), frappe.ValidationError)

	return enqueue_enrichment(reference_doctype, reference_name, website, frappe.session.user)


@frappe.whitelist()
@rate_limit(limit=ENRICH_RATE_LIMIT, seconds=60)
def enrich(reference_doctype: str, reference_name: str) -> dict:
	"""Enqueue a full enrichment run for one CRM record, using the record's own
	``website`` field. The initial trigger (the "Enrich from Website" button).

	Returns ``{queued: bool, job_id: str, website: str}``.
	"""
	cfg = get_config()
	doc = frappe.get_doc(reference_doctype, reference_name)
	website = (doc.get("website") or "").strip()
	return _enqueue_run(cfg, reference_doctype, reference_name, website)


@frappe.whitelist()
@rate_limit(limit=ENRICH_RATE_LIMIT, seconds=60)
def retry(run: str) -> dict:
	"""Re-run the enrichment recorded by a ``CRM Enrichment Run`` (the desk "Retry"
	button on each run). Re-enriches the run's linked record, preferring the record's
	current ``website`` and falling back to the website this run originally scraped.

	Returns ``{queued: bool, job_id: str, website: str}``.
	"""
	run_doc = frappe.get_doc("CRM Enrichment Run", run)
	if not run_doc.reference_doctype or not run_doc.reference_name:
		frappe.throw(_("This run has no linked record to re-enrich."), frappe.ValidationError)

	cfg = get_config()
	target = frappe.get_doc(run_doc.reference_doctype, run_doc.reference_name)
	website = (target.get("website") or "").strip() or (run_doc.source_website or "").strip()
	return _enqueue_run(cfg, run_doc.reference_doctype, run_doc.reference_name, website)
