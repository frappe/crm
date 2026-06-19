# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Background worker + the single run-writer.

``run_enrichment`` is the enqueued job: it runs the pipeline (streaming progress
over realtime), writes a ``CRM Enrichment Run`` history record, applies the mapper
to the origin document, and publishes a terminal event. It NEVER raises to the
worker -- every failure is recorded on the Run, logged via ``frappe.log_error`` and
reported over realtime.

``write_run`` is the ONLY place that persists run history, so the storage choice
(standalone Run doctype today) stays swappable.
"""

from __future__ import annotations

import frappe

from .config import get_config
from .mapper import apply_to_document
from .pipeline import PROGRESS_STEPS
from .pipeline import run as run_pipeline

# Realtime event the frontend (Phase 6) subscribes to.
PROGRESS_EVENT = "domain_enrichment_progress"

# Total number of pipeline progress steps (mirrors pipeline.PROGRESS_STEPS).
TOTAL_STEPS = len(PROGRESS_STEPS)


def _publish(reference_doctype, reference_name, status, message="", step=0, payload=None, user=None):
	"""Emit a single progress/terminal event. Mirrors crm/api/whatsapp.py shape:
	always carries the reference, plus step/total/message/status and an optional
	payload (terminal events put filled_fields/notes/result.flat() in the payload).
	Never raises -- realtime is best-effort."""
	try:
		frappe.publish_realtime(
			PROGRESS_EVENT,
			{
				"reference_doctype": reference_doctype,
				"reference_name": reference_name,
				"step": step,
				"total": TOTAL_STEPS,
				"message": message,
				"status": status,
				"payload": payload or {},
			},
			user=user,
		)
	except Exception:
		pass


def write_run(
	reference_doctype: str,
	reference_name: str,
	website: str,
	status: str,
	result=None,
	started_on=None,
	notes: str = "",
):
	"""Persist exactly one ``CRM Enrichment Run`` from an ``EnrichmentResult``.

	The single point of run-history writing -- storage stays swappable behind it.
	When ``result`` is given the summary fields + ``raw_json`` (full ``to_dict()``)
	are populated; otherwise a bare Run (status/website) is written.
	"""
	doc = frappe.new_doc("CRM Enrichment Run")
	doc.reference_doctype = reference_doctype
	doc.reference_name = reference_name
	doc.source_website = website
	doc.status = status
	doc.started_on = started_on or frappe.utils.now_datetime()
	if status in ("Completed", "Failed"):
		doc.finished_on = frappe.utils.now_datetime()
	if notes:
		doc.notes = notes

	if result is not None:
		social = ", ".join(sorted(result.social_profiles.keys()))
		doc.company_name = result.company_name.value or ""
		doc.industry = result.industry.value or ""
		doc.industry_confidence = result.industry_confidence or 0
		doc.emails_found = len(result.emails)
		doc.phones_found = len(result.phones)
		doc.social_profiles = social
		doc.raw_json = frappe.as_json(result.to_dict())
		if not notes and result.notes:
			doc.notes = "\n".join(result.notes)

	doc.insert(ignore_permissions=True)
	return doc.name


# DocType -> the Settings checkbox that gates auto-enrichment for it (mirrors
# api.ENABLE_FLAG_BY_DOCTYPE). Auto-enrich is wired (hooks.py after_insert) for the
# doctypes that own a ``website`` and are created standalone: Organization + Deal.
AUTO_ENRICH_FLAG_BY_DOCTYPE = {
	"CRM Lead": "enable_lead",
	"CRM Deal": "enable_deal",
	"CRM Organization": "enable_organization",
}


def auto_enrich_on_create(doc, method=None):
	"""``after_insert`` hook: auto-enqueue enrichment for a new CRM record.

	Wired for CRM Organization and CRM Deal. Best-effort and never raises into the
	save. Fires only when the feature is enabled, ``auto_enrich`` is on, the doctype is
	enabled, and the record has a website. Reuses the same per-doc ``job_id`` +
	``deduplicate`` as the manual ``api.enrich`` path, so a manual click and the
	auto-fire never double-run. A new Deal created with a website is therefore enriched
	alongside its Organization -- each crawls independently and writes its own fields.
	"""
	try:
		cfg = get_config()
		flag = AUTO_ENRICH_FLAG_BY_DOCTYPE.get(doc.doctype)
		if not (cfg.setting("enabled") and cfg.setting("auto_enrich") and flag and cfg.setting(flag)):
			return

		website = (doc.get("website") or "").strip()
		if not website:
			return

		timeout = int(cfg.setting("request_timeout", 10)) * int(cfg.setting("max_pages", 10)) + 60
		frappe.enqueue(
			"crm.domain_enrichment.tasks.run_enrichment",
			queue="long",
			timeout=timeout,
			job_id=f"domain-enrich-{doc.doctype}-{doc.name}",
			deduplicate=True,
			reference_doctype=doc.doctype,
			reference_name=doc.name,
			website=website,
			user=frappe.session.user,
		)
	except Exception:
		frappe.log_error(title="Domain Enrichment: auto_enrich_on_create failed")


def run_enrichment(reference_doctype: str, reference_name: str, website: str, user: str | None = None):
	"""Enqueued worker: crawl, map onto the origin doc, write a Run, stream progress.

	Never raises to the worker. On success the mapped origin doc is saved (a normal
	permission-respecting save -- it is the doc the user triggered enrichment on; no
	related records are touched, that is Phase 5). On any exception the Run is marked
	Failed, logged, and an error event is published.
	"""
	user = user or frappe.session.user
	started_on = frappe.utils.now_datetime()

	def progress(step_index, message=""):
		_publish(
			reference_doctype,
			reference_name,
			status="running",
			message=message,
			step=step_index,
			user=user,
		)

	try:
		cfg = get_config()
		_publish(reference_doctype, reference_name, status="running", message="Starting", step=0, user=user)

		result = run_pipeline(website, cfg=cfg, progress=progress)

		doc = frappe.get_doc(reference_doctype, reference_name)
		doc.check_permission("write")
		filled_fields = apply_to_document(doc, result, cfg)
		if filled_fields:
			doc.save()

		write_run(
			reference_doctype,
			reference_name,
			website,
			status="Completed",
			result=result,
			started_on=started_on,
		)

		_publish(
			reference_doctype,
			reference_name,
			status="completed",
			message="Completed",
			step=TOTAL_STEPS - 1,
			payload={
				"filled_fields": filled_fields,
				"notes": result.notes,
				**result.flat(),
			},
			user=user,
		)
	except Exception:
		frappe.log_error(
			title="Domain Enrichment: run_enrichment failed",
			message=frappe.get_traceback(),
		)
		try:
			write_run(
				reference_doctype,
				reference_name,
				website,
				status="Failed",
				started_on=started_on,
				notes=frappe.utils.cstr(frappe.get_traceback())[:1000],
			)
		except Exception:
			frappe.log_error(title="Domain Enrichment: could not write Failed run")
		_publish(
			reference_doctype,
			reference_name,
			status="error",
			message=frappe._("Enrichment failed. Check the error log."),
			step=0,
			user=user,
		)
