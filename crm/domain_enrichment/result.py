# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""EnrichmentResult schema. Preserves the {value, source, method} provenance shape.

Every piece of evidence keeps a ``source`` URL so any field can be traced back to
the page it was extracted from. Dataclasses serialize to plain dicts/JSON via
``to_dict()`` so the result can be returned by the engine and stored by the mapper /
run-writer (Phase 4) without any framework coupling. This module imports no framework
services on purpose -- it is the pure, unit-testable result container.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


# Canonical extraction-method labels -- every extracted value records which one
# produced it, so a reviewer can judge how much to trust it.
class Method:
	JSON_LD = "JSON-LD"
	META_TAG = "Meta Tag"
	TITLE_TAG = "Title Tag"
	BODY_TEXT = "Body Text"
	FAVICON = "Favicon"
	REGEX = "Regex"
	TEL_LINK = "tel: link"
	TEXT_HEURISTIC = "Text Heuristic"
	KEYWORD_CLASSIFIER = "Keyword Classifier"
	SOCIAL_RULE = "Social Rule"


@dataclass
class Email:
	value: str
	source: str = ""
	method: str = Method.REGEX

	def to_dict(self):
		return {"value": self.value, "source": self.source, "method": self.method}


@dataclass
class Phone:
	value: str  # normalized / cleaned
	raw: str = ""  # exactly as found on the page
	source: str = ""
	method: str = Method.REGEX

	def to_dict(self):
		return {
			"value": self.value,
			"raw": self.raw,
			"source": self.source,
			"method": self.method,
		}


@dataclass
class Field:
	"""A scalar value plus where/how it came from (company_name, description,
	logo, industry, ...)."""

	value: object = ""
	source: str = ""
	method: str = ""

	def to_dict(self):
		return {"value": self.value, "source": self.source, "method": self.method}


@dataclass
class SocialProfile:
	value: str = ""
	source: str = ""
	method: str = Method.SOCIAL_RULE

	def to_dict(self):
		return {"value": self.value, "source": self.source, "method": self.method}


@dataclass
class EnrichmentResult:
	website: str = ""
	# Scalar fields carry their own provenance via Field.
	company_name: Field = field(default_factory=Field)
	description: Field = field(default_factory=Field)
	logo: Field = field(default_factory=Field)
	industry: Field = field(default_factory=Field)
	industry_confidence: float = 0.0

	emails: list = field(default_factory=list)  # list[Email]
	phones: list = field(default_factory=list)  # list[Phone]
	social_profiles: dict = field(default_factory=dict)  # network -> SocialProfile

	# Diagnostics -- not part of the required schema but invaluable for debugging.
	pages_crawled: list = field(default_factory=list)
	errors: list = field(default_factory=list)
	notes: list = field(default_factory=list)  # human-readable warnings

	def to_dict(self):
		"""Render the canonical JSON schema. Every field is explainable: scalar
		fields expose {value, source, method}; list items embed source + method;
		social profiles are {value, source, method} per network."""
		return {
			"company_name": self.company_name.to_dict(),
			"description": self.description.to_dict(),
			"logo": self.logo.to_dict(),
			"industry": self.industry.to_dict(),
			"industry_confidence": round(self.industry_confidence, 2),
			"emails": [e.to_dict() for e in self.emails],
			"phones": [p.to_dict() for p in self.phones],
			"social_profiles": {k: v.to_dict() for k, v in self.social_profiles.items()},
			"_meta": {
				"website": self.website,
				"pages_crawled": self.pages_crawled,
				"errors": self.errors,
				"notes": self.notes,
			},
		}

	def flat(self):
		"""Convenience: collapse to plain scalar values (no provenance), useful
		for storing the headline fields on a Frappe document."""
		return {
			"company_name": self.company_name.value,
			"description": self.description.value,
			"logo": self.logo.value,
			"industry": self.industry.value,
			"industry_confidence": round(self.industry_confidence, 2),
			"social_profiles": {k: v.value for k, v in self.social_profiles.items()},
		}


@dataclass
class CrawledPage:
	"""A single fetched page and its parsed artifacts."""

	url: str
	status_code: int = 0
	html: str = ""
	text: str = ""
	title: str = ""
	headings: list = field(default_factory=list)
	error: str = ""

	def to_dict(self):
		return asdict(self)
