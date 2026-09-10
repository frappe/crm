# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Settings access for the Registry Enrichment feature.

Thin, framework-cached reads of the ``CRM Registry Enrichment Settings`` Single plus
the field-mapping rows embedded in it. The hot path (the per-insert auto-enrich gate)
only touches the Single, never assembling anything heavier. The token lives in a
Password field and is read via ``get_password`` so it is decrypted on demand and never
kept in the cached doc's plain attributes.
"""

from __future__ import annotations

from dataclasses import dataclass

import frappe

# Doctypes registry enrichment runs on in phase 1 (Organization and Lead by CNPJ).
# Single source of truth shared by the manual (api) and auto-enrich (tasks) paths and
# the allow-list the whitelisted API checks a caller-supplied doctype against.
ENRICHABLE_DOCTYPES = ("CRM Organization", "CRM Lead")

# The CNPJ package used in phase 1 (package 6 / CNPJ D: the richest CNPJ package).
CNPJ_PACKAGE = 6

# Fallback per-request timeout (seconds) when Settings has not been saved yet.
DEFAULT_TIMEOUT = 15


@dataclass
class Mapping:
	"""One field-mapping row consumed by ``mapper.apply_to_document``."""

	source_key: str
	target_doctype: str
	target_fieldname: str
	write_policy: str = "Fill if empty"
	create_missing_link: int = 0


def get_settings():
	"""The ``CRM Registry Enrichment Settings`` Single, framework-cached. Cheap: reads
	only the Single, so it is safe on the per-insert auto-enrich hot path."""
	return frappe.get_cached_doc("CRM Registry Enrichment Settings")


def is_enabled() -> bool:
	"""True when the feature master switch is on."""
	return bool(get_settings().get("enabled"))


def get_token() -> str:
	"""The decrypted API token, or ``""`` when unset. Never raises."""
	return get_settings().get_password("api_token", raise_exception=False) or ""


def get_timeout() -> int:
	"""The configured per-request timeout in seconds, falling back to the default."""
	value = get_settings().get("request_timeout")
	return int(value) if value else DEFAULT_TIMEOUT


def auto_enrich_enabled_for(doctype: str) -> bool:
	"""True if auto-enrich-on-create should fire for ``doctype``: a cheap Settings-only
	check (feature enabled + auto_enrich on + an enrichable doctype)."""
	s = get_settings()
	return bool(s.get("enabled") and s.get("auto_enrich") and doctype in ENRICHABLE_DOCTYPES)


def get_mappings(doctype: str) -> list[Mapping]:
	"""The enabled field mappings targeting ``doctype`` (from the Settings child table)."""
	settings = get_settings()
	mappings = []
	for row in settings.field_mappings or []:
		if not row.enabled or row.target_doctype != doctype:
			continue
		mappings.append(
			Mapping(
				source_key=row.source_key,
				target_doctype=row.target_doctype,
				target_fieldname=row.target_fieldname,
				write_policy=row.write_policy or "Fill if empty",
				create_missing_link=row.create_missing_link or 0,
			)
		)
	return mappings
