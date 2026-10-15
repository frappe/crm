# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Whitelisted entry points: ``enrich`` (enqueue a full run for a record),
``retry`` (re-run one from its Run history), ``undo`` (revert a record's newest
run that changed fields), ``get_status`` (whether a run is in flight, to resume the
Enrich button after a refresh) and ``get_enriched_fields`` (fields runs wrote).

All are type-annotated -- hooks.py sets ``require_type_annotated_api_methods``.
Security: ``enrich`` / ``retry`` / ``undo`` enforce the doctype allow-list (from
Settings) + a ``write`` permission check and are rate-limited per user (see
``ENRICH_RATE_LIMIT``); ``get_status`` / ``get_enriched_fields`` need ``read``
on the record.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import cstr, now_datetime
from frappe.utils.background_jobs import is_job_enqueued

from .config import ENRICHABLE_DOCTYPES, EnrichmentConfig, get_config
from .doctype.crm_enrichment_run.crm_enrichment_run import restore_value
from .mapper import POLICY_ALWAYS_REFRESH
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


def _completed_runs(reference_doctype: str, reference_name: str) -> list[str]:
	"""The record's Completed ``CRM Enrichment Run`` names, newest first. Reverted
	and Failed runs wrote nothing that still stands, so they are left out."""
	return frappe.get_all(
		"CRM Enrichment Run",
		filters={
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"status": "Completed",
		},
		pluck="name",
		order_by="creation desc",
	)


def _run_changes(runs: list[str]) -> dict[str, list]:
	"""The Change rows of ``runs``, grouped by run name, in row order."""
	if not runs:
		return {}
	rows = frappe.get_all(
		"CRM Enrichment Run Change",
		filters={"parenttype": "CRM Enrichment Run", "parent": ["in", runs]},
		fields=["parent", "fieldname", "new_value"],
		order_by="idx asc",
	)
	out = {}
	for row in rows:
		out.setdefault(row.parent, []).append(row)
	return out


def _undoable_run(runs: list[str]) -> str | None:
	"""The run Undo targets: the newest of ``runs`` (Completed, newest first) that
	changed at least one field. A re-enrich that found nothing new is skipped, so
	Undo still reaches the run that wrote the values."""
	changed = _run_changes(runs)
	return next((run for run in runs if run in changed), None)


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
	"""Revert the fields written by the record's newest Completed enrichment run
	that changed fields (a re-enrich that changed nothing is skipped). The newer
	Completed runs that changed nothing only confirmed the values just reverted,
	so they are marked Reverted too. Blocked while an enrichment job for the
	record is queued or running.

	Returns ``{reverted: [fieldname, ...], skipped: [fieldname, ...]}``.
	"""
	_check_writable(get_config(), reference_doctype, reference_name)

	if is_job_enqueued(enrichment_job_id(reference_doctype, reference_name)):
		frappe.throw(
			_("Enrichment is still running for this record. Try again once it finishes."),
			frappe.ValidationError,
		)

	runs = _completed_runs(reference_doctype, reference_name)
	run = _undoable_run(runs)
	if not run:
		frappe.throw(_("There is no enrichment to undo for this record."), frappe.ValidationError)

	out = frappe.get_doc("CRM Enrichment Run", run).undo()
	# Runs are newest first, so every run before the target changed nothing.
	for newer in runs[: runs.index(run)]:
		frappe.db.set_value(
			"CRM Enrichment Run",
			newer,
			{"status": "Reverted", "undone_on": now_datetime(), "undone_by": frappe.session.user},
		)
	return out


@frappe.whitelist()
def get_status(reference_doctype: str, reference_name: str) -> dict:
	"""Whether an enrichment job for the record is queued or running, and the
	newest run's status (``None`` before any run), so a page opened mid-run can
	show it and tell whether it succeeded once it ends.

	Returns ``{running: bool, last_run_status: str | None}``.
	"""
	frappe.get_doc(reference_doctype, reference_name).check_permission("read")

	return {
		"running": is_job_enqueued(enrichment_job_id(reference_doctype, reference_name)),
		"last_run_status": frappe.db.get_value(
			"CRM Enrichment Run",
			{"reference_doctype": reference_doctype, "reference_name": reference_name},
			"status",
			order_by="creation desc",
		),
	}


@frappe.whitelist()
def get_enriched_fields(reference_doctype: str, reference_name: str) -> list[dict]:
	"""The fields the record's enrichment runs wrote, for the Data tab's
	enriched-field icon and the re-enrich warning.

	Covers every Completed run (a Reverted or Failed run wrote nothing that still
	stands); a field written by several runs is reported from the newest. A run
	records only the fields it changed, so a re-enrich that found the same values
	leaves the earlier run's entries in place. Each entry is ``{fieldname, label,
	value, edited, refreshes}``: ``value`` is what the newest run wrote, cast to the
	field's type so the client can compare it with an unsaved value; ``edited`` is
	whether the saved record no longer holds it (compared like ``Run.undo``);
	``refreshes`` is whether re-enriching overwrites the field even after the user
	edited it (an "Always refresh" mapping).
	"""
	doc = frappe.get_doc(reference_doctype, reference_name)
	doc.check_permission("read")

	runs = _completed_runs(reference_doctype, reference_name)
	if not runs:
		return []

	refreshed = {
		mapping.target_fieldname
		for mapping in get_config().mappings_by_doctype.get(reference_doctype, [])
		if mapping.write_policy == POLICY_ALWAYS_REFRESH
	}
	changes_by_run = _run_changes(runs)
	out, seen = [], set()
	for run in runs:
		for change in changes_by_run.get(run, []):
			# Runs are newest first, so the first change seen for a field wins.
			if change.fieldname in seen:
				continue
			seen.add(change.fieldname)
			df = doc.meta.get_field(change.fieldname)
			if not df:
				continue
			value = restore_value(df, change.new_value)
			out.append(
				{
					"fieldname": change.fieldname,
					"label": _(df.label),
					"value": value,
					"edited": cstr(doc.get(change.fieldname)) != cstr(value),
					"refreshes": change.fieldname in refreshed,
				}
			)
	return out
