# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Single source of result -> CRM field logic, driven by Field Mapping records.

``apply_to_document`` is the ONLY place that translates an ``EnrichmentResult``
into CRM document fields. Phase 5's link-time Organization -> Lead/Deal copy reuses
it, so all the write-policy / has-field / never-overwrite guards live here once.

The mapping itself is data: each ``CRM Enrichment Field Mapping`` record names a
``source_key`` (one of the 15 frozen in Phase 2), a ``target_fieldname``, a
``write_policy`` (Fill if empty / Always refresh / Override defaults) and optional
``default_values`` / ``create_missing_link``. This module knows how to resolve a
``source_key`` against the result and how to apply each policy -- nothing else.
"""

from __future__ import annotations

from urllib.parse import urlparse

import frappe
from frappe import _

# Human labels for the realtime "filled: ..." toast, keyed by source_key. Falls
# back to the field's meta label, then the fieldname, when not listed here.
SOURCE_KEY_LABELS = {
	"company_name": _("Organization Name"),
	"description": _("Company Description"),
	"logo": _("Logo"),
	"industry": _("Industry"),
	"primary_email": _("Email"),
	"primary_phone": _("Phone"),
	"secondary_phone": _("Phone"),
	"linkedin": _("LinkedIn"),
	"twitter": _("X (Twitter)"),
	"github": _("GitHub"),
	"facebook": _("Facebook"),
	"instagram": _("Instagram"),
	"youtube": _("YouTube"),
}

# source_keys backed by a social_profiles[<network>] entry on the result.
_SOCIAL_KEYS = ("linkedin", "twitter", "github", "facebook", "instagram", "youtube")

# Write-policy constants (must match the CRM Enrichment Field Mapping Select options).
POLICY_FILL_IF_EMPTY = "Fill if empty"
POLICY_ALWAYS_REFRESH = "Always refresh"
POLICY_OVERRIDE_DEFAULTS = "Override defaults"


def _registrable_domain(url: str) -> str:
	"""Registrable domain, e.g. "frappe.io" from "https://crm.frappe.io/x"."""
	netloc = (urlparse(url or "").netloc or "").lower().split(":")[0]
	if netloc.startswith("www."):
		netloc = netloc[4:]
	return ".".join(netloc.split(".")[-2:]) if netloc.count(".") >= 1 else netloc


def _first_email(result) -> str:
	"""Prefer an email on the company's own registrable domain, else the first.

	Mirrors the POC behaviour: a sales address on the company's own domain is a
	better company contact than a random third-party address picked up elsewhere.
	"""
	if not result.emails:
		return ""
	registrable = _registrable_domain(result.website)
	if registrable:
		for e in result.emails:
			if e.value.lower().split("@")[-1].endswith(registrable):
				return e.value
	return result.emails[0].value


def _phone_at(result, index: int) -> str:
	"""The raw (else cleaned) phone at ``index``; falls back to the primary."""
	if not result.phones:
		return ""
	if index >= len(result.phones):
		index = 0
	p = result.phones[index]
	return p.raw or p.value


def get_value_for_source_key(result, source_key: str):
	"""Resolve one of the 15 frozen source_keys against an ``EnrichmentResult``.

	Returns a plain scalar (``""`` means "nothing to fill"). Scalar provenance
	fields expose ``.value``; emails/phones/contacts are read off the result's
	lists; social profiles off ``result.social_profiles[<network>]``.
	"""
	if source_key == "company_name":
		return result.company_name.value or ""
	if source_key == "description":
		return result.description.value or ""
	if source_key == "logo":
		return result.logo.value or ""
	if source_key == "industry":
		return result.industry.value or ""
	if source_key == "primary_email":
		return _first_email(result)
	if source_key == "primary_phone":
		return _phone_at(result, 0)
	if source_key == "secondary_phone":
		return _phone_at(result, 1)
	if source_key in _SOCIAL_KEYS:
		profile = result.social_profiles.get(source_key)
		return profile.value if profile else ""
	return ""


def _ensure_link_target(target_doctype: str, target_fieldname: str, value: str):
	"""For a Link field with ``create_missing_link`` set, auto-create the linked
	master if it is missing. Explicit, opt-in -- never a hidden side effect.

	Returns the value to write (the linked name) or ``None`` to skip the field.
	Any failure is swallowed (the field is skipped, the run is not aborted).
	"""
	meta = frappe.get_meta(target_doctype)
	df = meta.get_field(target_fieldname)
	if not df or df.fieldtype != "Link" or not df.options:
		# Not a Link (or unknown field) -- nothing to create; write as-is.
		return value
	link_doctype = df.options
	if frappe.db.exists(link_doctype, value):
		return value
	try:
		link_meta = frappe.get_meta(link_doctype)
		new_doc = {"doctype": link_doctype}
		# Populate the field the master autonames from (e.g. CRM Industry.industry),
		# falling back to the title field, so the created record's name == value.
		autoname = link_meta.autoname or ""
		if autoname.startswith("field:"):
			new_doc[autoname.split(":", 1)[1]] = value
		elif link_meta.get_title_field():
			new_doc[link_meta.get_title_field()] = value
		else:
			new_doc["__newname"] = value
		frappe.get_doc(new_doc).insert(ignore_permissions=True)
		return value
	except Exception:
		frappe.log_error(
			title="Domain Enrichment: could not create link master",
			message=f"{link_doctype}={value!r} for {target_doctype}.{target_fieldname}",
		)
		return None


def _label_for(doc, source_key: str, target_fieldname: str) -> str:
	if source_key in SOURCE_KEY_LABELS:
		return SOURCE_KEY_LABELS[source_key]
	df = doc.meta.get_field(target_fieldname)
	return df.label if df and df.label else target_fieldname


def _overridable_defaults(mapping) -> set:
	"""The set of "really unset" default values for an Override-defaults mapping
	(newline-separated in ``default_values``), e.g. {"", "1-10"}."""
	defaults = {""}
	for line in (mapping.default_values or "").splitlines():
		token = line.strip()
		if token:
			defaults.add(token)
	return defaults


def apply_to_document(doc, result, cfg, fill_empty_only: bool = False) -> list[str]:
	"""Populate mappable fields on a Lead / Deal / Organization from ``result``.

	Driven by ``cfg.mappings_by_doctype[doc.doctype]`` (the enabled Field Mapping
	records). For each mapping the value is resolved by ``source_key`` and written
	according to ``write_policy``:

	* **Fill if empty** -- set only when the doc field is currently empty.
	* **Always refresh** -- overwrite (or clear) with the fresh value; this is how
	  stale guesses get cleaned on re-enrichment.
	* **Override defaults** -- treat the mapping's ``default_values`` as empty and
	  fill over them, else respect a real user value.

	When ``fill_empty_only`` is True every mapping is forced to fill-empty semantics
	regardless of its configured ``write_policy`` (and empty source values are never
	written). This is the link-time Organization -> Lead/Deal copy path (Phase 5),
	which must never overwrite or clear user-entered data.

	Never overwrites real user-entered data except per the policies above. Does NOT
	save the document -- the caller controls persistence/permissions. Returns the
	human labels of the fields that were changed.
	"""
	filled: list[str] = []
	mappings = cfg.mappings_by_doctype.get(doc.doctype, [])

	for mapping in mappings:
		fieldname = mapping.target_fieldname
		if not doc.meta.has_field(fieldname):
			continue
		value = get_value_for_source_key(result, mapping.source_key)
		label = _label_for(doc, mapping.source_key, fieldname)
		current = doc.get(fieldname)
		policy = POLICY_FILL_IF_EMPTY if fill_empty_only else (mapping.write_policy or POLICY_FILL_IF_EMPTY)

		if policy == POLICY_ALWAYS_REFRESH:
			# Overwrite (or clear) with the fresh value, even if empty.
			if current == value:
				continue
			if value and mapping.create_missing_link:
				value = _ensure_link_target(doc.doctype, fieldname, value)
				if value is None:
					continue
			doc.set(fieldname, value)
			if value and label not in filled:
				filled.append(label)
			continue

		# Fill-if-empty / Override-defaults both require a non-empty fresh value.
		if not value:
			continue

		if policy == POLICY_OVERRIDE_DEFAULTS:
			overridable = _overridable_defaults(mapping)
			if current and current not in overridable:
				continue  # a real user value -- respect it
		else:  # Fill if empty
			if current:
				continue

		if current == value:
			continue

		if mapping.create_missing_link:
			value = _ensure_link_target(doc.doctype, fieldname, value)
			if value is None:
				continue

		doc.set(fieldname, value)
		if label not in filled:
			filled.append(label)

	return filled
