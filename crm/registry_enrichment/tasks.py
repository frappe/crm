# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Background worker, run-writer and the auto-enrich-on-create trigger.

``run_enrichment`` is the enqueued job: it reads the record's ``tax_id``, validates
it, looks the CNPJ up, normalizes the payload, applies the field mappings to the
origin document, records a ``CRM Registry Enrichment Run`` and streams progress over
realtime. It NEVER raises to the worker: every failure is recorded on the Run, logged
via ``frappe.log_error`` and reported over realtime.

``write_run`` is the ONLY place run history is persisted (it upserts a single row
through the Queued/Running/Completed/Failed lifecycle), so the storage choice stays
swappable.
"""

from __future__ import annotations

import frappe
from frappe import _

from . import client
from .config import (
	CNPJ_PACKAGE,
	auto_enrich_enabled_for,
	get_mappings,
	get_timeout,
	get_token,
)
from .mapper import apply_to_document
from .normalizer import to_result
from .validators import is_valid_cnpj, normalize_document

# Realtime event the frontend subscribes to.
PROGRESS_EVENT = "registry_enrichment_progress"

# Savepoint the worker rolls back to on failure. Rolling back to a NAMED savepoint (not
# a full ``frappe.db.rollback()``) discards only the worker's own partial writes -- the
# Running run row and any partial ``doc.save`` -- while leaving the surrounding
# transaction intact. A full rollback would also unwind the savepoint an
# ``IntegrationTestCase`` wraps each test in, so the error path could not be tested.
_SAVE_POINT = "registry_enrichment_run"

# Payload keys carrying personal data (partners, contacts, the responsible person). They
# are stripped before the payload is persisted to a Run so no CPF / personal contact
# lands in run history (LGPD data minimization).
_PERSONAL_KEYS = frozenset({"socios", "qsa", "responsavel", "responsavelCpf", "email", "telefones"})

# Account / response metadata that is not company registry data: the remaining query
# credit (``saldo``), the lookup id (``consultaID``), the server-side delay, the package
# used and the response status. Dropped from Run history so it only ever holds the
# company's registry data, not the CPF.CNPJ account's state.
_METADATA_KEYS = frozenset({"saldo", "consultaID", "delay", "pacoteUsado", "status"})

# Every key stripped before a payload is persisted to a Run.
_REDACTED_KEYS = _PERSONAL_KEYS | _METADATA_KEYS


def _redact_payload(payload: dict | None) -> dict:
	"""Return a shallow copy of ``payload`` with personal-data and account-metadata keys
	removed.

	Run history keeps only the fiscal/company view of the lookup: names of partners, the
	responsible person, contact email and phone numbers (personal data, LGPD data
	minimization), plus account/response metadata (``saldo``, ``consultaID``, ``delay``,
	``pacoteUsado``, ``status``) are all dropped so a Run stores neither personal data
	nor the querying account's state."""
	if not isinstance(payload, dict):
		return {}
	return {key: value for key, value in payload.items() if key not in _REDACTED_KEYS}


INFLIGHT_TIMEOUT_MINUTES = 15


def find_inflight_run(reference_doctype: str, reference_name: str) -> str | None:
	"""Name of a live in-flight (Queued or Running) Run for this record, or ``None``.

	Both enqueue paths share one per-doc ``job_id`` with ``deduplicate=True``, so a
	manual click racing an ``after_insert`` auto-fire (or two concurrent clicks) can
	have its second enqueue silently dropped. Reusing the in-flight Run instead of
	pre-creating another Queued row keeps that second attempt from stranding an orphan
	Run that never resolves: the manual path short-circuits to it, and the worker adopts
	it when the auto path enqueued with no pre-created run.

	An in-flight Run that has not moved for ``INFLIGHT_TIMEOUT_MINUTES`` is treated as
	lost (worker crash, dropped queue) and is marked Failed so a new attempt can start
	instead of being short-circuited forever."""
	rows = frappe.get_all(
		"CRM Registry Enrichment Run",
		filters={
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"status": ("in", ("Queued", "Running")),
		},
		fields=["name", "modified"],
		order_by="modified desc",
	)
	if not rows:
		return None
	cutoff = frappe.utils.add_to_date(frappe.utils.now_datetime(), minutes=-INFLIGHT_TIMEOUT_MINUTES)
	live = None
	for row in rows:
		if live is None and frappe.utils.get_datetime(row.modified) >= cutoff:
			live = row.name
			continue
		frappe.db.set_value(
			"CRM Registry Enrichment Run",
			row.name,
			{
				"status": "Failed",
				"error": _("Timed out waiting for the background worker."),
				"finished_at": frappe.utils.now_datetime(),
			},
			update_modified=True,
		)
	return live


def _publish(reference_doctype, reference_name, status, fields_updated=0, error=None, user=None):
	"""Emit one progress/terminal event on the flat contract the frontend consumes.

	The payload is flat: ``{reference_doctype, reference_name, status, fields_updated,
	error}`` where ``status`` is one of queued/running/completed/failed. Never raises --
	realtime is best-effort."""
	try:
		frappe.publish_realtime(
			PROGRESS_EVENT,
			{
				"reference_doctype": reference_doctype,
				"reference_name": reference_name,
				"status": status,
				"fields_updated": int(fields_updated or 0),
				"error": error,
			},
			user=user,
		)
	except Exception:
		pass


def write_run(
	reference_doctype: str,
	reference_name: str,
	document_number: str,
	status: str,
	run: str | None = None,
	error: str = "",
	fields_updated: int = 0,
	raw_payload: dict | None = None,
	started_at=None,
) -> str:
	"""Upsert exactly one ``CRM Registry Enrichment Run`` and return its name.

	When ``run`` names an existing row it is updated in place (the Queued -> Running ->
	terminal transitions); otherwise a fresh row is inserted. The single point of
	run-history writing -- storage stays swappable behind it.

	Only a REDACTED copy of ``raw_payload`` is persisted to ``raw_json``: personal-data
	keys (partners, responsible person, contact email/phones) are stripped by
	``_redact_payload`` so run history holds no personal data (LGPD data minimization).
	"""
	if run and frappe.db.exists("CRM Registry Enrichment Run", run):
		doc = frappe.get_doc("CRM Registry Enrichment Run", run)
		is_new = False
	else:
		doc = frappe.new_doc("CRM Registry Enrichment Run")
		doc.reference_doctype = reference_doctype
		doc.reference_name = reference_name
		doc.started_at = started_at or frappe.utils.now_datetime()
		is_new = True

	doc.document_number = document_number
	doc.status = status
	doc.fields_updated = fields_updated
	if error:
		doc.error = frappe.utils.cstr(error)[:1000]
	if raw_payload is not None:
		doc.raw_json = frappe.as_json(_redact_payload(raw_payload))
	if status in ("Completed", "Failed"):
		doc.finished_at = frappe.utils.now_datetime()

	if is_new:
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)
	return doc.name


def enqueue_enrichment(
	reference_doctype: str, reference_name: str, run: str | None = None, trigger: str = "manual"
) -> dict:
	"""Enqueue one ``run_enrichment`` job (long queue, per-doc ``job_id`` +
	``deduplicate``, after commit).

	The single place the job is enqueued -- shared by the manual (``api.enrich`` /
	``api.retry``) and auto (``after_insert``) paths, so a manual click and an
	auto-fire never double-run and the enqueue options stay in one spot.
	``enqueue_after_commit`` matters for the ``after_insert`` caller, whose transaction
	has not committed yet; it is harmless for the already-saved paths. ``run`` is the
	pre-created Queued Run the manual path hands the job so its lifecycle stays one row.
	"""
	job_id = f"registry-enrich-{reference_doctype}-{reference_name}"
	frappe.enqueue(
		"crm.registry_enrichment.tasks.run_enrichment",
		queue="long",
		timeout=get_timeout() + 60,
		job_id=job_id,
		deduplicate=True,
		enqueue_after_commit=True,
		reference_doctype=reference_doctype,
		reference_name=reference_name,
		run=run,
		user=frappe.session.user,
		trigger=trigger,
	)
	return {"queued": True, "job_id": job_id}


def auto_enrich_on_create(doc, method=None):
	"""Auto-enqueue enrichment for a new CRM Lead / Organization.

	Called from the ``after_insert`` of the controllers (the trigger stays visible
	where the record lives, rather than as a doc_events hook). Best-effort and never
	raises into the save: it fires only when the feature is enabled, ``auto_enrich`` is
	on, the doctype is enabled and the record already carries a valid CNPJ in
	``tax_id``. Reuses the same per-doc ``job_id`` + ``deduplicate`` as the manual path.
	"""
	try:
		if not auto_enrich_enabled_for(doc.doctype):
			return
		document = normalize_document(doc.get("tax_id") or "")
		if not is_valid_cnpj(document):
			return
		enqueue_enrichment(doc.doctype, doc.name, trigger="auto")
	except Exception:
		frappe.log_error(title="Registry Enrichment: auto_enrich_on_create failed")


def run_enrichment(
	reference_doctype: str,
	reference_name: str,
	run: str | None = None,
	user: str | None = None,
	trigger: str = "manual",
):
	"""Enqueued worker: look the CNPJ up, map onto the origin doc, write a Run, stream
	progress.

	Never raises to the worker. On success the mapped origin doc is saved (a normal
	permission-respecting save). On any failure the worker's own partial writes are
	rolled back to a named savepoint, the failure is logged, a Failed Run is written and
	a failed event is published.
	"""
	user = user or frappe.session.user
	started_at = frappe.utils.now_datetime()
	document = ""

	try:
		# Savepoint before any write so a failure unwinds only the worker's partials
		# (the Running row, a partial doc.save) without touching the surrounding
		# transaction. tax_id is read inside the try so a read failure is recorded too.
		frappe.db.savepoint(_SAVE_POINT)
		document = normalize_document(frappe.db.get_value(reference_doctype, reference_name, "tax_id") or "")

		doc = frappe.get_doc(reference_doctype, reference_name)
		doc.check_permission("write")

		if not is_valid_cnpj(document):
			raise ValueError(frappe._("The record does not have a valid CNPJ in Tax ID."))

		token = get_token()
		if not token:
			raise ValueError(frappe._("The registry API token is not configured."))

		# Adopt a Run the manual path may have pre-created (job-id dedupe can drop its
		# enqueue), so an auto-fire that arrived with run=None never strands it Queued.
		if not run:
			run = find_inflight_run(reference_doctype, reference_name)

		run = write_run(
			reference_doctype,
			reference_name,
			document,
			status="Running",
			run=run,
			started_at=started_at,
		)
		_publish(reference_doctype, reference_name, status="running", user=user)

		payload = client.fetch(document, CNPJ_PACKAGE, token, get_timeout())
		result = to_result(payload)

		mappings = get_mappings(reference_doctype)
		filled_fields = apply_to_document(doc, result, mappings)
		if filled_fields:
			doc.save()

		write_run(
			reference_doctype,
			reference_name,
			document,
			status="Completed",
			run=run,
			fields_updated=len(filled_fields),
			raw_payload=payload,
		)
		_publish(
			reference_doctype,
			reference_name,
			status="completed",
			fields_updated=len(filled_fields),
			user=user,
		)
	except Exception as exc:
		# Discard any partial writes (the Running Run row and a doc.save that fired
		# before a later step threw). execute_job commits on normal return, so without
		# the rollback those partials would land alongside the Failed run. Rolling back
		# to the worker's own savepoint keeps the outer transaction (and, under tests,
		# the IntegrationTestCase savepoint) intact.
		frappe.db.rollback(save_point=_SAVE_POINT)
		frappe.log_error(
			title="Registry Enrichment: run_enrichment failed",
			message=frappe.get_traceback(),
		)
		message = getattr(exc, "message", None) or frappe.utils.cstr(exc)
		try:
			write_run(
				reference_doctype,
				reference_name,
				document,
				status="Failed",
				run=run,
				error=message,
				started_at=started_at,
			)
		except Exception:
			frappe.log_error(title="Registry Enrichment: could not write Failed run")
		_publish(
			reference_doctype,
			reference_name,
			status="failed",
			error=message,
			user=user,
		)
