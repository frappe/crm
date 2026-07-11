# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Whitelisted entry points: ``enrich`` (enqueue full run) and ``enrich_preview``
(bounded, fast, synchronous prefill).

Both are type-annotated -- hooks.py sets ``require_type_annotated_api_methods``.
Security: enrich enforces the doctype allow-list (from Settings) + a ``write``
permission check; enrich_preview is rate-limited per user and SSRF-checked (the
engine enforces SSRF, we don't bypass it).
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit

from .config import ENABLE_FLAG_BY_DOCTYPE, EnrichmentConfig, get_config
from .mapper import get_value_for_source_key
from .pipeline import run as run_pipeline
from .tasks import enqueue_enrichment


def _enabled_doctypes(cfg: EnrichmentConfig) -> list[str]:
	"""The doctypes enrichment is enabled for, per Settings (allow-list)."""
	if not cfg.setting("enabled"):
		return []
	return [dt for dt, flag in ENABLE_FLAG_BY_DOCTYPE.items() if cfg.setting(flag)]


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

	return enqueue_enrichment(cfg, reference_doctype, reference_name, website, frappe.session.user)


@frappe.whitelist()
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


@frappe.whitelist()
@rate_limit(limit=10, seconds=60)
def enrich_preview(website: str, doctype: str = "CRM Deal") -> dict:
	"""Bounded, fast, synchronous prefill for the create-record modal.

	Runs the pipeline with the Settings preview bounds (homepage-only /
	``preview_max_pages``, short ``preview_timeout``), SSRF enforced by the engine.
	Maps the result to the given doctype's Field Mapping. No DB writes, no doc, no
	job -- returns quickly.

	Returns ``{fields: {fieldname: value}, notes: [...]}``.
	"""
	website = (website or "").strip()
	if not website:
		frappe.throw(_("A website is required."), frappe.ValidationError)

	cfg = get_config()
	if doctype not in _enabled_doctypes(cfg):
		frappe.throw(
			_("Enrichment is not enabled for {0}.").format(doctype),
			frappe.ValidationError,
		)

	# Build a bounded copy of the config: homepage-only crawl, short timeout. The
	# engine still enforces SSRF.
	preview_settings = dict(cfg.settings)
	preview_settings["max_pages"] = cfg.setting("preview_max_pages", 1)
	preview_settings["max_depth"] = 0
	preview_settings["request_timeout"] = cfg.setting("preview_timeout", 8)
	preview_cfg = EnrichmentConfig(
		settings=preview_settings,
		rules_by_type=cfg.rules_by_type,
		mappings_by_doctype=cfg.mappings_by_doctype,
		link_priority=cfg.link_priority,
		skip_patterns=cfg.skip_patterns,
		allowed_domains=cfg.allowed_domains,
		blocked_domains=cfg.blocked_domains,
	)

	result = run_pipeline(website, cfg=preview_cfg)

	fields: dict = {}
	for mapping in preview_cfg.mappings_by_doctype.get(doctype, []):
		value = get_value_for_source_key(result, mapping.source_key)
		if value:
			fields[mapping.target_fieldname] = value

	return {"fields": fields, "notes": result.notes}
