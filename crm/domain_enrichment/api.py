# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Whitelisted entry points: ``enrich`` (enqueue a full run for a record),
``retry`` (re-run one from its Run history), ``undo`` (revert a record's latest
run) and ``get_status`` (the Enrich button's state for a record).

All are type-annotated -- hooks.py sets ``require_type_annotated_api_methods``.
Security: ``enrich`` / ``retry`` / ``undo`` enforce the doctype allow-list (from
Settings) + a ``write`` permission check and are rate-limited per user (see
``ENRICH_RATE_LIMIT``); ``get_status`` needs ``read`` on the record.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils.background_jobs import is_job_enqueued

from .config import ENRICHABLE_DOCTYPES, EnrichmentConfig, get_config
from .tasks import enqueue_enrichment, enrichment_job_id

# Per-user, per-minute cap on each enrich entry point (each gets its own bucket).
# Both only enqueue a per-doc-deduplicated job -- 10/min is far above any real human
# burst while capping scripted queue-flooding.
ENRICH_RATE_LIMIT = 10


def _enabled_doctypes(cfg: EnrichmentConfig) -> list[str]:
	"""The doctypes enrichment is enabled for, per Settings (allow-list)."""
	if not cfg.setting("enabled"):
		return []
	return list(ENRICHABLE_DOCTYPES)


def _check_writable(cfg, reference_doctype: str, reference_name: str):
	"""Enforce the Settings allow-list and ``write`` permission on a target record."""
	if reference_doctype not in _enabled_doctypes(cfg):
		frappe.throw(
			_("Enrichment is not enabled for {0}.").format(reference_doctype),
			frappe.ValidationError,
		)

	doc = frappe.get_doc(reference_doctype, reference_name)
	doc.check_permission("write")


def _latest_run(reference_doctype: str, reference_name: str):
	"""The record's most recent ``CRM Enrichment Run`` name, or ``None``."""
	return frappe.db.get_value(
		"CRM Enrichment Run",
		{"reference_doctype": reference_doctype, "reference_name": reference_name},
		"name",
		order_by="creation desc",
	)


def _can_undo(run: str | None) -> bool:
	"""Whether ``run`` is Completed and wrote at least one field."""
	if not run or frappe.db.get_value("CRM Enrichment Run", run, "status") != "Completed":
		return False
	return bool(
		frappe.db.exists("CRM Enrichment Run Change", {"parent": run, "parenttype": "CRM Enrichment Run"})
	)


def _enqueue_run(cfg, reference_doctype: str, reference_name: str, website: str) -> dict:
	"""Validate + enqueue one enrichment run for a target record. Shared by
	``enrich`` (initial trigger from the record) and ``retry`` (re-run from a Run).

	Caller must have already resolved the website. Enforces the Settings allow-list
	and ``write`` permission on the target. Uses the per-doc ``job_id`` +
	``deduplicate`` so a second trigger while one is in-flight is a no-op.
	"""
	_check_writable(cfg, reference_doctype, reference_name)

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


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=ENRICH_RATE_LIMIT, seconds=60)
def undo(reference_doctype: str, reference_name: str) -> dict:
	"""Revert the fields written by the record's latest enrichment run.

	Only the latest run can be undone, and only when it is Completed and changed
	fields -- the same rule as ``get_status``'s ``can_undo``. Blocked while an
	enrichment job for the record is queued or running.

	Returns ``{reverted: [fieldname, ...], skipped: [fieldname, ...]}``.
	"""
	_check_writable(get_config(), reference_doctype, reference_name)

	if is_job_enqueued(enrichment_job_id(reference_doctype, reference_name)):
		frappe.throw(
			_("Enrichment is still running for this record. Try again once it finishes."),
			frappe.ValidationError,
		)

	run = _latest_run(reference_doctype, reference_name)
	if not _can_undo(run):
		frappe.throw(_("There is no enrichment to undo for this record."), frappe.ValidationError)

	return frappe.get_doc("CRM Enrichment Run", run).undo()


@frappe.whitelist()
def get_status(reference_doctype: str, reference_name: str) -> dict:
	"""The Enrich button's state for one record.

	Returns ``{has_website: bool, state: "idle" | "running" | "done", can_undo: bool}``.
	``running`` while a job is queued/running, ``done`` when the latest run
	Completed, else ``idle`` (never enriched, failed, or reverted).
	"""
	doc = frappe.get_doc(reference_doctype, reference_name)
	doc.check_permission("read")

	run = _latest_run(reference_doctype, reference_name)
	if is_job_enqueued(enrichment_job_id(reference_doctype, reference_name)):
		state = "running"
	elif run and frappe.db.get_value("CRM Enrichment Run", run, "status") == "Completed":
		state = "done"
	else:
		state = "idle"

	return {
		"has_website": bool((doc.get("website") or "").strip()),
		"state": state,
		"can_undo": _can_undo(run),
	}
