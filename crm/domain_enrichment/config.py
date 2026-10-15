# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Loads enrichment configuration (Settings + Rules + Field Mappings) from the desk.

The engine is rule-agnostic: it loads admin-edited config here and executes it.
``get_config()`` assembles an ``EnrichmentConfig`` from the config doctypes on demand
(not cached -- see the note on ``get_config``). Hot paths that only need the Settings
toggles use ``get_settings`` / ``auto_enrich_enabled_for`` instead of the full build.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import frappe

# DocType -> the Settings checkbox that enables enrichment for it. Single source of
# truth shared by the manual (api) and auto-enrich (tasks) paths.
ENABLE_FLAG_BY_DOCTYPE = {
	"CRM Lead": "enable_lead",
	"CRM Deal": "enable_deal",
	"CRM Organization": "enable_organization",
}


# Sensible fallbacks applied when the Single doctype has not been saved yet (the
# JSON field defaults only populate a freshly-created row, which may not exist).
DEFAULT_SETTINGS = {
	"enabled": 1,
	"enable_lead": 1,
	"enable_deal": 1,
	"enable_organization": 1,
	"auto_enrich": 0,
	"max_pages": 10,
	"max_depth": 2,
	"use_sitemap": 1,
	"request_timeout": 10,
	"max_download_bytes": 3_000_000,
	"retry_count": 2,
	"user_agent": (
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
		"(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
	),
	"preview_max_pages": 1,
	"preview_timeout": 8,
}


def _setting(doc, key):
	"""One Settings field, falling back to DEFAULT_SETTINGS when unset."""
	val = doc.get(key)
	return DEFAULT_SETTINGS.get(key) if val in (None, "") else val


def get_settings():
	"""The CRM Enrichment Settings Single, framework-cached via ``get_cached_doc``.

	Cheap: reads only the Single, never assembling Rules/Mappings. For hot paths --
	the per-insert auto-enrich flag check and the enqueue timeout -- that must not
	build the full config on every record creation.
	"""
	return frappe.get_cached_doc("CRM Enrichment Settings")


def auto_enrich_enabled_for(doctype: str) -> bool:
	"""True if auto-enrich-on-create should fire for ``doctype``. A cheap,
	Settings-only check (feature enabled + auto_enrich on + this doctype enabled) --
	no Rules/Mappings assembled."""
	s = get_settings()
	flag = ENABLE_FLAG_BY_DOCTYPE.get(doctype)
	return bool(_setting(s, "enabled") and _setting(s, "auto_enrich") and flag and _setting(s, flag))


# Industry classifier thresholds. These are mechanics (how confident the winner
# must be), not tunable knowledge, so they stay constants. If an admin ever needs
# to tune them they can be promoted to Settings fields without touching callers.
INDUSTRY_MIN_SCORE = 2  # at least one headline keyword hit (weighted)
INDUSTRY_MIN_CONFIDENCE = 0.34  # the winner must clearly lead

# Default link-priority ordering (BFS) -- seeded into Settings.link_priority_order
# on install, and used as a fallback when that table is empty.
DEFAULT_LINK_PRIORITY = [
	("about", 1.0),
	("contact", 1.0),
	("team", 1.0),
	("leadership", 1.0),
	("careers", 1.0),
	("company", 1.0),
	("people", 1.0),
	("founders", 1.0),
	("management", 1.0),
	("jobs", 1.0),
]


@dataclass
class Rule:
	"""A single config-driven rule with its compiled patterns.

	``patterns`` is a list of (compiled_regex, raw_pattern) tuples. Substring
	patterns (is_regex=0) are compiled as escaped, case-insensitive regexes so the
	executors can use one uniform match path.
	"""

	rule_type: str
	target_value: str = ""
	industry: str = ""
	weight: float = 1.0
	match_scope: str = "Full Text"
	patterns: list = field(default_factory=list)

	@property
	def label(self) -> str:
		"""The value a match yields: industry name for Industry rules, else
		target_value (tech name / network)."""
		return self.industry if self.rule_type == "Industry" else self.target_value

	def matches(self, text: str) -> int:
		"""Total number of pattern hits across this rule's patterns in ``text``."""
		if not text:
			return 0
		return sum(len(rx.findall(text)) for rx, _raw in self.patterns)


@dataclass
class Mapping:
	source_key: str
	target_doctype: str
	target_fieldname: str
	write_policy: str = "Fill if empty"
	create_missing_link: int = 0
	default_values: str = ""


@dataclass
class EnrichmentConfig:
	settings: dict = field(default_factory=dict)
	rules_by_type: dict = field(default_factory=dict)  # rule_type -> list[Rule]
	mappings_by_doctype: dict = field(default_factory=dict)  # doctype -> list[Mapping]
	link_priority: list = field(default_factory=list)  # list[(keyword, weight)]
	skip_patterns: list = field(default_factory=list)  # list[str]
	allowed_domains: list = field(default_factory=list)
	blocked_domains: list = field(default_factory=list)

	# Convenience accessors with fallbacks --------------------------------- #
	def setting(self, key, default=None):
		val = self.settings.get(key)
		if val in (None, ""):
			return DEFAULT_SETTINGS.get(key, default)
		return val

	def rules(self, rule_type: str) -> list:
		return self.rules_by_type.get(rule_type, [])


def _compile_pattern(pattern: str, is_regex: int):
	try:
		if is_regex:
			return re.compile(pattern, re.IGNORECASE)
		# Word-boundary-anchor substring patterns: an un-anchored short keyword like
		# "erp" or "api" matches inside completely unrelated words ("waterproofing",
		# "capital"), causing false industry-classification hits. An admin who wants
		# unanchored substring matching can still opt in via is_regex=1.
		return re.compile(rf"\b{re.escape(pattern)}\b", re.IGNORECASE)
	except re.error:
		# A malformed admin-entered regex must not break the whole config build.
		frappe.log_error(
			title="Domain Enrichment: invalid rule pattern",
			message=f"Could not compile pattern: {pattern!r}",
		)
		return None


def _build_rules() -> dict:
	rules_by_type: dict = {}
	names = frappe.get_all("CRM Enrichment Rule", filters={"enabled": 1}, pluck="name")
	for name in names:
		doc = frappe.get_doc("CRM Enrichment Rule", name)
		compiled = []
		for pat in doc.patterns or []:
			rx = _compile_pattern(pat.pattern, pat.is_regex)
			if rx is not None:
				compiled.append((rx, pat.pattern))
		if not compiled:
			continue
		rule = Rule(
			rule_type=doc.rule_type,
			target_value=doc.target_value or "",
			industry=doc.industry or "",
			weight=doc.weight or 1.0,
			match_scope=doc.match_scope or "Full Text",
			patterns=compiled,
		)
		rules_by_type.setdefault(doc.rule_type, []).append(rule)
	return rules_by_type


def _build_mappings() -> dict:
	mappings_by_doctype: dict = {}
	rows = frappe.get_all(
		"CRM Enrichment Field Mapping",
		filters={"enabled": 1},
		fields=[
			"source_key",
			"target_doctype",
			"target_fieldname",
			"write_policy",
			"create_missing_link",
			"default_values",
		],
	)
	for row in rows:
		mapping = Mapping(
			source_key=row.source_key,
			target_doctype=row.target_doctype,
			target_fieldname=row.target_fieldname,
			write_policy=row.write_policy or "Fill if empty",
			create_missing_link=row.create_missing_link or 0,
			default_values=row.default_values or "",
		)
		mappings_by_doctype.setdefault(row.target_doctype, []).append(mapping)
	return mappings_by_doctype


def _build_settings(settings_doc) -> dict:
	out = {}
	for key in DEFAULT_SETTINGS:
		out[key] = settings_doc.get(key)
	return out


def _build_config() -> EnrichmentConfig:
	settings_doc = frappe.get_cached_doc("CRM Enrichment Settings")

	link_priority = [
		(kw.keyword.lower(), kw.weight or 1.0)
		for kw in (settings_doc.link_priority_order or [])
		if kw.keyword
	] or list(DEFAULT_LINK_PRIORITY)

	skip_patterns = [sp.pattern for sp in (settings_doc.skip_patterns or []) if sp.pattern]

	allowed_domains = [d.domain.lower().strip() for d in (settings_doc.allowed_domains or []) if d.domain]
	blocked_domains = [d.domain.lower().strip() for d in (settings_doc.blocked_domains or []) if d.domain]

	return EnrichmentConfig(
		settings=_build_settings(settings_doc),
		rules_by_type=_build_rules(),
		mappings_by_doctype=_build_mappings(),
		link_priority=link_priority,
		skip_patterns=skip_patterns,
		allowed_domains=allowed_domains,
		blocked_domains=blocked_domains,
	)


def get_config() -> EnrichmentConfig:
	"""Assemble the full enrichment config (Settings + Rules + Field Mappings) fresh.

	Deliberately NOT cached. It is built at most a couple of times per enrichment run,
	and a run is a multi-second, network-bound crawl -- so the handful of small queries
	here is noise. A cache, by contrast, buys nothing measurable and adds a real
	stale-config surface (any write that bypasses ``on_update`` -- a bulk ``db_set``,
	direct SQL -- would serve stale rules until a restart). The per-insert hot path does
	NOT call this; it uses ``auto_enrich_enabled_for`` (Settings-only). Do not re-add a
	cache here without a measured hot-path caller that justifies it.
	"""
	return _build_config()
