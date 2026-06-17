# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Frappe integration layer for Website Intelligence.

Thin glue around the framework-free `crm.website_intelligence` pipeline:

  * `enrich_from_website`  — whitelisted; validates the request and enqueues a job
  * `run_enrichment`       — background worker; runs the pipeline, streams the 9
                             progress steps over realtime, stores the result on
                             the document's `website_intelligence` child table.

The heavy lifting (crawl + extract) lives in the standalone package so it stays
testable without a site.
"""

import json

import frappe
from frappe import _
from frappe.utils import now_datetime

from crm.website_intelligence import WebsiteIntelligencePipeline
from crm.website_intelligence.pipeline import PROGRESS_STEPS

# Only these doctypes expose the feature.
ALLOWED_DOCTYPES = ("CRM Lead", "CRM Organization", "CRM Deal")
REALTIME_EVENT = "website_intelligence_progress"


@frappe.whitelist()
def enrich_from_website(reference_doctype: str, reference_name: str):
    """Queue an enrichment job for a Lead/Organization. Returns the job id.

    Raises if the doctype is unsupported or the document has no website.
    """
    if reference_doctype not in ALLOWED_DOCTYPES:
        frappe.throw(_("Website Intelligence is not available for {0}").format(reference_doctype))

    # Permission check — the user must be able to write the document.
    doc = frappe.get_doc(reference_doctype, reference_name)
    doc.check_permission("write")

    website = (doc.get("website") or "").strip()
    if not website:
        frappe.throw(_("Set a Website on this record before enriching."))

    job = frappe.enqueue(
        "crm.api.website_intelligence.run_enrichment",
        queue="long",
        timeout=300,
        reference_doctype=reference_doctype,
        reference_name=reference_name,
        website=website,
        user=frappe.session.user,
        # de-dupe: a second click while one is running is a no-op
        job_id=f"website-intel-{reference_doctype}-{reference_name}",
        deduplicate=True,
    )
    return {"queued": True, "job_id": getattr(job, "id", None), "website": website}


@frappe.whitelist()
def get_enrichment_for_website(website: str, doctype: str = "CRM Deal"):
    """Synchronously crawl a website and return field values to PREFILL a form
    (e.g. the Create Deal modal) — no document, no DB writes, no background job.

    Returns {"fields": {fieldname: value, ...}, "notes": [...]}. `fields` is mapped
    via the same FIELD_MAP getters used by the saved-doc flow, so the modal gets the
    exact field names it can assign onto its form object. A blocked/unreachable site
    yields empty `fields` plus a human-readable `notes` message for a toast.
    """
    if doctype not in ALLOWED_DOCTYPES:
        frappe.throw(_("Website Intelligence is not available for {0}").format(doctype))

    website = (website or "").strip()
    if not website:
        frappe.throw(_("Enter a website to enrich."))

    # Keep the crawl small so the (synchronous) call stays responsive behind a spinner.
    result = WebsiteIntelligencePipeline(website, max_pages=2).run()

    light_doc = {"website": website}
    fields = {}
    for fieldname, getter in FIELD_MAP.get(doctype, {}).items():
        value = getter(result, light_doc)
        if value:
            fields[fieldname] = value
    return {"fields": fields, "notes": result.notes}


def _publish(user, reference_doctype, reference_name, step_index, message,
             status="running", payload=None):
    frappe.publish_realtime(
        REALTIME_EVENT,
        {
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
            "step": step_index + 1,
            "total": len(PROGRESS_STEPS),
            "message": message,
            "status": status,
            "payload": payload or {},
        },
        user=user,
    )


def run_enrichment(reference_doctype, reference_name, website, user=None):
    """Background entry point. Never raises to the worker — failures are reported
    over realtime and recorded on the document."""
    def progress(step_index, message):
        _publish(user, reference_doctype, reference_name, step_index, message)

    try:
        result = WebsiteIntelligencePipeline(website, progress=progress).run()
        filled = _store_result(reference_doctype, reference_name, result)
        # A Deal links to an Organization; if it has none, find-or-create one from
        # the enrichment and link it (so the company shows on the Deal).
        linked_org = _ensure_linked_organization(reference_doctype, reference_name, result)
        # Fan the same result out to linked records for the same company (e.g. a
        # Deal's Organization and source Lead) — fills empty fields only.
        propagated = _propagate_to_related(reference_doctype, reference_name, result)
        payload = result.flat()
        payload["filled_fields"] = filled
        payload["propagated_to"] = [f"{dt}: {name}" for dt, name in propagated]
        payload["linked_organization"] = linked_org
        payload["notes"] = result.notes
        _publish(user, reference_doctype, reference_name,
                 len(PROGRESS_STEPS) - 1, _("Completed"), status="completed",
                 payload=payload)
    except Exception:
        frappe.log_error(
            title="Website Intelligence enrichment failed",
            message=frappe.get_traceback(),
        )
        _publish(user, reference_doctype, reference_name, len(PROGRESS_STEPS) - 1,
                 _("Enrichment failed — see Error Log."), status="error")


def _store_result(reference_doctype, reference_name, result):
    """Persist one enrichment run as a child-table row + lightweight doc updates."""
    flat = result.flat()
    row = {
        "crawl_date": now_datetime(),
        "company_description": flat["description"][:1000],
        "industry": flat["industry"],
        # Field is a Percent (0-100); confidence is 0-1.
        "industry_confidence": round((flat["industry_confidence"] or 0) * 100, 2),
        "technologies": ", ".join(t.name for t in result.technologies),
        "emails_found": "\n".join(e.value for e in result.emails),
        "phones_found": "\n".join(p.raw or p.value for p in result.phones),
        "social_profiles": json.dumps(
            {k: v.value for k, v in result.social_profiles.items() if v.value},
            indent=2,
        ),
        "contacts_found": "\n".join(
            f"{c.name} — {c.designation}" for c in result.contacts
        ),
        "hiring_signal": int(result.signals.hiring),
        "funding_signal": int(result.signals.funding),
        "ai_signal": int(result.signals.ai),
        "raw_json": json.dumps(result.to_dict(), indent=2, ensure_ascii=False),
    }

    doc = frappe.get_doc(reference_doctype, reference_name)
    doc.append("website_intelligence", row)

    # Fill empty document fields from the enrichment, never overwriting data the
    # user already entered. Returns the human labels of what was actually filled.
    filled = _apply_to_document(doc, result)

    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return filled


def _registrable_domain(url):
    """Registrable domain, e.g. "frappe.io" from "https://crm.frappe.io/x"."""
    from urllib.parse import urlparse

    netloc = (urlparse(url or "").netloc or "").lower().split(":")[0]
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return ".".join(netloc.split(".")[-2:]) if netloc.count(".") >= 1 else netloc


def _first_email(result, website):
    """Prefer an email on the company's own registrable domain, else the first."""
    if not result.emails:
        return ""
    registrable = _registrable_domain(website)
    if registrable:
        for e in result.emails:
            if e.value.lower().split("@")[-1].endswith(registrable):
                return e.value
    return result.emails[0].value


# --------------------------------------------------------------------------- #
# Result -> CRM field mapping
#
# The enrichment result has a FIXED schema (guaranteed by EnrichmentResult — every
# key is always present, empty values are "" / []), so the mapping from result to
# CRM document fields is a declarative table rather than hand-written branches.
# Each getter is a pure fn (result, doc) -> value; "" means "nothing to fill".
# Add a CRM field => add one row. set_if_empty() applies the has-field +
# never-overwrite guards uniformly.
# --------------------------------------------------------------------------- #
def _website(result, doc):
    """The enriched URL — fills an empty website on related records so they can be
    re-enriched. No-op on the origin (its website is already set)."""
    return result.website


def _name(result, doc):
    return result.flat()["company_name"]


def _description(result, doc):
    return result.flat()["description"]


def _employees(result, doc):
    """CRM `no_of_employees` select bucket (e.g. "11-50") or "" if not found."""
    return result.flat()["employees"]


def _logo(result, doc):
    return result.flat()["logo"]


def _industry(result, doc):
    """Industry is a Link to CRM Industry. The classifier emits a small fixed
    vocabulary (SaaS, CRM, ERP, …), so auto-create the master if it's missing,
    then link it. Falls back to "" if creation fails."""
    industry = result.flat()["industry"]
    if not industry:
        return ""
    if not frappe.db.exists("CRM Industry", industry):
        try:
            frappe.get_doc({"doctype": "CRM Industry", "industry": industry}).insert(
                ignore_permissions=True)
        except Exception:
            return ""
    return industry


def _best_email(result, doc):
    return _first_email(result, doc.get("website") or "")


def _phone1(result, doc):
    if not result.phones:
        return ""
    return result.phones[0].raw or result.phones[0].value


def _phone2(result, doc):
    """Second number if there is one, else mirror the primary (matches the prior
    behaviour of populating both mobile_no and phone)."""
    if not result.phones:
        return ""
    p = result.phones[1] if len(result.phones) > 1 else result.phones[0]
    return p.raw or p.value


def _social(network):
    """Getter for a social profile URL (e.g. linkedin, twitter)."""
    def get(result, doc):
        profile = result.social_profiles.get(network)
        return profile.value if profile else ""
    return get


def _key_people(result, doc):
    """Discovered team members as a "Name — Title" summary, one per line."""
    return "\n".join(f"{c.name} — {c.designation}" for c in result.contacts)


# Social links, signals and team — shared across all three doctypes.
_ENRICHMENT_EXTRAS = {
    "linkedin": _social("linkedin"),
    "twitter": _social("twitter"),
    "key_people": _key_people,
}

# fieldname -> getter. The same `organization` name string must NOT go onto CRM
# Deal's `organization` field (a Link to CRM Organization); Deal uses the
# free-text `organization_name` instead.
FIELD_MAP = {
    # Contact fields (email/mobile/phone) and address are intentionally NOT filled
    # by enrichment — those belong to a person, not the company website.
    "CRM Lead": {
        "website": _website,
        "organization": _name,
        "organization_logo": _logo,
        "company_description": _description,
        "industry": _industry,
        "no_of_employees": _employees,
        **_ENRICHMENT_EXTRAS,
    },
    # CRM Deal's email/mobile_no are derived from its primary contact (cleared on
    # save by set_primary_email_mobile_no), so enrichment can't set them — omit.
    "CRM Deal": {
        "website": _website,
        "organization_name": _name,
        "organization_logo": _logo,
        "company_description": _description,
        "industry": _industry,
        "no_of_employees": _employees,
        **_ENRICHMENT_EXTRAS,
    },
    # CRM Organization has no email/mobile_no/phone fields.
    "CRM Organization": {
        "website": _website,
        "organization_name": _name,
        "organization_logo": _logo,
        "company_description": _description,
        "industry": _industry,
        "no_of_employees": _employees,
        **_ENRICHMENT_EXTRAS,
    },
}

# Human labels for the realtime "filled: …" toast.
FIELD_LABELS = {
    "website": _("Website"),
    "organization": _("Organization Name"),
    "organization_name": _("Organization Name"),
    "organization_logo": _("Logo"),
    "company_description": _("Company Description"),
    "industry": _("Industry"),
    "no_of_employees": _("No. of Employees"),
    "email": _("Email"),
    "mobile_no": _("Mobile No"),
    "phone": _("Phone"),
    "linkedin": _("LinkedIn"),
    "twitter": _("X (Twitter)"),
    "key_people": _("Key People"),
}


# Values that are really "unset" defaults — enrichment may override these even
# though they're non-empty. `no_of_employees` shows "1-10" (the first Select
# option) by default, which would otherwise block enrichment from ever filling it.
OVERRIDABLE_DEFAULTS = {
    "no_of_employees": {"", "1-10"},
}

# Read-only, fully enrichment-derived fields (the user never types these), so each
# enrichment refreshes them — even clearing a stale value — rather than leaving old
# data in place. This is how re-enriching cleans up earlier bad guesses.
ALWAYS_REFRESH = {"key_people"}


def _apply_to_document(doc, result):
    """Populate empty, mappable fields on a Lead / Deal / Organization.

    Driven by FIELD_MAP. Existing user data is left intact, except for fields whose
    current value is a known meaningless default (see OVERRIDABLE_DEFAULTS) or which
    are fully enrichment-derived (ALWAYS_REFRESH). Returns the labels filled.
    """
    filled = []

    def set_if_empty(fieldname, value, label):
        if not value:
            return
        if not doc.meta.has_field(fieldname):
            return
        current = doc.get(fieldname)
        overridable = OVERRIDABLE_DEFAULTS.get(fieldname)
        # Respect a real user value; treat a known default as if it were empty.
        if current and not (overridable and current in overridable):
            return
        if current == value:
            return  # already correct — nothing to do
        doc.set(fieldname, value)
        if label not in filled:
            filled.append(label)

    for fieldname, getter in FIELD_MAP.get(doc.doctype, {}).items():
        value = getter(result, doc)
        label = FIELD_LABELS.get(fieldname, fieldname)
        if fieldname in ALWAYS_REFRESH:
            # Overwrite (or clear) the stored value with the fresh result.
            if doc.meta.has_field(fieldname) and doc.get(fieldname) != value:
                doc.set(fieldname, value)
                if value and label not in filled:
                    filled.append(label)
            continue
        set_if_empty(fieldname, value, label)

    return filled


# --------------------------------------------------------------------------- #
# Cross-doctype propagation
#
# CRM links related records by company: a Deal points to an Organization
# (`organization`) and a source Lead (`lead`). When one is enriched, fan the same
# result out to the others so the company's logo/name/industry/website appear
# everywhere — filling empty fields only (same guards as the origin).
# --------------------------------------------------------------------------- #
PROPAGATION_CAP = 50  # bound fan-out for an Organization with many Deals


def _related_documents(doctype, name):
    """(doctype, name) pairs linked to the enriched record by company."""
    rels = []
    if doctype == "CRM Deal":
        deal = frappe.db.get_value(
            "CRM Deal", name, ["organization", "lead"], as_dict=True) or {}
        if deal.get("organization"):
            rels.append(("CRM Organization", deal["organization"]))
        if deal.get("lead"):
            rels.append(("CRM Lead", deal["lead"]))
    elif doctype == "CRM Organization":
        deals = frappe.get_all("CRM Deal", filters={"organization": name},
                               pluck="name", limit=PROPAGATION_CAP)
        rels += [("CRM Deal", d) for d in deals]
        for lead in frappe.get_all(
                "CRM Deal", filters={"name": ["in", deals]}, pluck="lead") if deals else []:
            if lead:
                rels.append(("CRM Lead", lead))
    elif doctype == "CRM Lead":
        deals = frappe.get_all("CRM Deal", filters={"lead": name},
                               pluck="name", limit=PROPAGATION_CAP)
        rels += [("CRM Deal", d) for d in deals]
        for org in frappe.get_all(
                "CRM Deal", filters={"name": ["in", deals]}, pluck="organization") if deals else []:
            if org:
                rels.append(("CRM Organization", org))

    # Dedupe, drop the origin itself.
    seen, out = set(), []
    for r in rels:
        if r not in seen and r != (doctype, name):
            seen.add(r)
            out.append(r)
    return out


def _same_company(doc, enriched_website):
    """Guard: only propagate into a record whose website is empty or shares the
    enriched registrable domain — so we never paint a different company's data."""
    existing = (doc.get("website") or "").strip()
    if not existing:
        return True
    return _registrable_domain(existing) == _registrable_domain(enriched_website)


def _propagate_to_related(origin_doctype, origin_name, result):
    """Apply the enrichment to linked records. Returns the (doctype, name) list
    that actually changed. Never raises — propagation is best-effort."""
    updated = []
    for dt, name in _related_documents(origin_doctype, origin_name)[:PROPAGATION_CAP]:
        try:
            doc = frappe.get_doc(dt, name)
            if not _same_company(doc, result.website):
                continue
            if _apply_to_document(doc, result):
                doc.save(ignore_permissions=True)
                updated.append((dt, name))
        except Exception:
            # One bad linked record must not fail the whole enrichment.
            frappe.log_error(
                title="Website Intelligence propagation failed",
                message=f"{dt} {name}\n{frappe.get_traceback()}",
            )
    return updated


def _find_organization(name, website):
    """Locate an existing CRM Organization by exact name or by website domain."""
    if name and frappe.db.exists("CRM Organization", name):
        return name
    domain = _registrable_domain(website)
    if domain:
        match = frappe.get_all(
            "CRM Organization", filters=[["website", "like", f"%{domain}%"]],
            pluck="name", limit=1)
        if match:
            return match[0]
    return None


def _ensure_linked_organization(reference_doctype, reference_name, result):
    """For a Deal with no linked Organization, find-or-create one from the
    enrichment and link it. Returns the organization name, or None.

    A Deal's `organization` is a Link to CRM Organization, so a free-text company
    name can't be stored there — without this, the Organization field stays empty.
    """
    if reference_doctype != "CRM Deal":
        return None
    name = result.flat()["company_name"]
    if not name:
        return None  # nothing reliable to name an organization after (e.g. blocked site)

    doc = frappe.get_doc("CRM Deal", reference_name)
    if doc.get("organization"):
        return None  # already linked — propagation handles filling it

    try:
        org_name = _find_organization(name, result.website)
        if not org_name:
            org = frappe.new_doc("CRM Organization")
            org.organization_name = name
            org.website = result.website
            _apply_to_document(org, result)  # logo, description, industry, employees…
            org.insert(ignore_permissions=True)
            org_name = org.name
        doc.organization = org_name
        doc.save(ignore_permissions=True)
        return org_name
    except Exception:
        frappe.log_error(
            title="Website Intelligence: organization creation failed",
            message=f"{reference_name}\n{frappe.get_traceback()}",
        )
        return None
