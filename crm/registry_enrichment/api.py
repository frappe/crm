# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Whitelisted entry points: ``enrich`` (enqueue a run for a record), ``retry``
(re-run one from its Run history) and ``get_settings_status`` (a small UI probe).

Both write paths are type-annotated (hooks.py sets
``require_type_annotated_api_methods``). Security: each enforces the phase-1 doctype
allow-list, a ``write`` permission check on the target, and validates the CNPJ before
enqueuing a paid lookup, and both are rate-limited per user.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit

from . import tasks
from .config import ENRICHABLE_DOCTYPES, get_token, is_enabled
from .validators import is_valid_cnpj, normalize_document

# Per-user, per-minute cap on each enrich entry point (each gets its own bucket). Both
# only enqueue a per-doc-deduplicated job -- 10/min is far above any real human burst
# while capping scripted queue-flooding.
ENRICH_RATE_LIMIT = 10

# Higher per-user cap for the read-only settings probe. The UI calls it on load, so it
# needs more headroom than the enqueue paths, but it still must not be an unmetered
# endpoint a script can hammer.
STATUS_RATE_LIMIT = 60


def _guard(reference_doctype: str, reference_name: str):
	"""Shared validation for the enqueue paths: feature enabled + token present, the
	phase-1 allow-list, a ``write`` permission check, and a valid CNPJ in ``tax_id``.

	Returns the loaded target document. Raises a user-friendly ``ValidationError`` on
	any failed precondition so the UI shows an actionable message.
	"""
	if not is_enabled():
		frappe.throw(_("Registry enrichment is disabled. Enable it in Settings."), frappe.ValidationError)

	if not get_token():
		frappe.throw(_("Set the registry API token in Settings before enriching."), frappe.ValidationError)

	if reference_doctype not in ENRICHABLE_DOCTYPES:
		frappe.throw(
			_("Registry enrichment is not available for {0}.").format(reference_doctype),
			frappe.ValidationError,
		)

	doc = frappe.get_doc(reference_doctype, reference_name)
	doc.check_permission("write")

	if not is_valid_cnpj(normalize_document(doc.get("tax_id") or "")):
		frappe.throw(_("Set a valid CNPJ in Tax ID before enriching."), frappe.ValidationError)

	return doc


def _queue_run(reference_doctype: str, reference_name: str, document: str) -> dict:
	"""Create the Queued Run, enqueue the job against it, and return the UI contract.

	The Run row is created up front (status Queued) so the frontend has a handle to
	track before the worker starts, and the same row is carried through the
	Running/Completed/Failed lifecycle. Returns ``{queued: True, run: <run name>}``.

	If a Run is already in flight for this record (an auto-fire or a concurrent click),
	it is reused rather than pre-creating a second Queued row: the shared per-doc
	``job_id`` would dedupe the second enqueue and leave that row orphaned.
	"""
	existing = tasks.find_inflight_run(reference_doctype, reference_name)
	if existing:
		return {"queued": True, "run": existing}
	run = tasks.write_run(reference_doctype, reference_name, document, status="Queued")
	tasks.enqueue_enrichment(reference_doctype, reference_name, run=run)
	tasks._publish(reference_doctype, reference_name, status="queued", user=frappe.session.user)
	return {"queued": True, "run": run}


@frappe.whitelist()
@rate_limit(limit=ENRICH_RATE_LIMIT, seconds=60)
def enrich(reference_doctype: str, reference_name: str) -> dict:
	"""Enqueue an enrichment run for one CRM record, using its own ``tax_id`` (CNPJ).

	Returns ``{queued: bool, run: str}`` where ``run`` names the Queued Run created for
	the frontend to track.
	"""
	doc = _guard(reference_doctype, reference_name)
	document = normalize_document(doc.get("tax_id") or "")
	return _queue_run(reference_doctype, reference_name, document)


@frappe.whitelist()
@rate_limit(limit=ENRICH_RATE_LIMIT, seconds=60)
def retry(run: str) -> dict:
	"""Re-run the enrichment recorded by a ``CRM Registry Enrichment Run`` (the desk
	"Retry" action on a run). Re-enriches the run's linked record from its current
	``tax_id``.

	Requires ``read`` on the source Run as well as ``write`` on the target record, so a
	caller cannot re-run against a Run they are not allowed to see. Returns
	``{queued: bool, run: str}`` naming the fresh Queued Run.
	"""
	if not frappe.has_permission("CRM Registry Enrichment Run", "read", run):
		raise frappe.PermissionError

	run_doc = frappe.get_doc("CRM Registry Enrichment Run", run)
	if not run_doc.reference_doctype or not run_doc.reference_name:
		frappe.throw(_("This run has no linked record to re-enrich."), frappe.ValidationError)

	doc = _guard(run_doc.reference_doctype, run_doc.reference_name)
	document = normalize_document(doc.get("tax_id") or "")
	return _queue_run(run_doc.reference_doctype, run_doc.reference_name, document)


@frappe.whitelist()
@rate_limit(limit=STATUS_RATE_LIMIT, seconds=60)
def get_settings_status() -> dict:
	"""Small UI probe: whether the feature is enabled and whether a token is set (never
	returns the token itself)."""
	return {"enabled": is_enabled(), "has_token": bool(get_token())}
