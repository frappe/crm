# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Loads enrichment configuration (Settings + Rules + Field Mappings) from the desk.

The engine is rule-agnostic: it loads admin-edited config here and executes it.
``get_config()`` returns a cached ``EnrichmentConfig`` assembled from the three
Phase 2 config doctypes; it is invalidated by ``clear_config_cache`` (wired to the
config doctypes' doc_events in hooks.py).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import frappe

# Cache key holding the assembled config. Built lazily by get_config() and cleared
# whenever any of the three config doctypes changes (see hooks.py doc_events ->
# clear_config_cache).
CONFIG_CACHE_KEY = "domain_enrichment_config"

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
	"request_timeout": 10,
	"max_download_bytes": 3_000_000,
	"retry_count": 2,
	"user_agent": (
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
		"(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
	),
	"preview_max_pages": 1,
	"preview_timeout": 8,
	"allow_private_networks": 0,
}

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
		return re.compile(re.escape(pattern), re.IGNORECASE)
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
	"""Return the cached, assembled enrichment config.

	Caches the assembled ``EnrichmentConfig`` object (not a plain dict -- the config
	carries compiled regexes) via ``frappe.cache().get_value`` with a generator that
	rebuilds it on a cache miss. The generator returns the dataclass directly; frappe's
	RedisWrapper pickles it -- compiled patterns pickle fine under cPickle, so this
	is safe and avoids re-querying on every call within a request/worker.
	"""
	return frappe.cache().get_value(CONFIG_CACHE_KEY, generator=_build_config)


def clear_config_cache(doc=None, method=None):
	"""Drop the cached enrichment config.

	Wired to on_update / on_trash of CRM Enrichment Settings / Rule / Field
	Mapping so an admin edit takes effect on the next enrichment without a
	restart. The ``doc``/``method`` signature matches Frappe doc_event hooks.
	"""
	frappe.cache().delete_value(CONFIG_CACHE_KEY)
