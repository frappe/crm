"""Dataclasses describing an enrichment result.

Every piece of evidence keeps a `source` URL so any field can be traced back to
the page it was extracted from. Dataclasses serialize to plain dicts/JSON via
`to_dict()` so the result can be returned by the CLI and stored by Frappe without
any framework coupling.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


def _dedupe_keep_order(items):
    """Deduplicate a list while preserving first-seen order (case-insensitive
    for strings)."""
    seen = set()
    out = []
    for it in items:
        key = it.lower() if isinstance(it, str) else it
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


# Canonical extraction-method labels — every extracted value records which one
# produced it, so a reviewer can judge how much to trust it.
class Method:
    JSON_LD = "JSON-LD"
    META_TAG = "Meta Tag"
    TITLE_TAG = "Title Tag"
    FAVICON = "Favicon"
    REGEX = "Regex"
    TEL_LINK = "tel: link"
    TECH_RULE = "Technology Rule"
    TEAM_RULE = "Team Rule"
    TEXT_HEURISTIC = "Text Heuristic"
    KEYWORD_CLASSIFIER = "Keyword Classifier"
    SOCIAL_RULE = "Social Rule"
    EMPLOYEE_HEURISTIC = "Employee Heuristic"
    WIKIPEDIA = "Wikipedia"


@dataclass
class Email:
    value: str
    source: str = ""
    method: str = Method.REGEX

    def to_dict(self):
        return {"value": self.value, "source": self.source, "method": self.method}


@dataclass
class Phone:
    value: str          # normalized / cleaned
    raw: str = ""       # exactly as found on the page
    source: str = ""
    method: str = Method.REGEX

    def to_dict(self):
        return {"value": self.value, "raw": self.raw,
                "source": self.source, "method": self.method}


@dataclass
class Address:
    value: str
    source: str = ""
    confidence: float = 0.0   # 0.0 - 1.0
    method: str = Method.JSON_LD

    def to_dict(self):
        return {
            "value": self.value,
            "source": self.source,
            "confidence": round(self.confidence, 2),
            "method": self.method,
        }


@dataclass
class Contact:
    name: str
    designation: str = ""
    source: str = ""
    confidence: float = 0.0
    method: str = Method.TEAM_RULE

    def to_dict(self):
        return {
            "name": self.name,
            "designation": self.designation,
            "source": self.source,
            "confidence": round(self.confidence, 2),
            "method": self.method,
        }


@dataclass
class Technology:
    name: str
    source: str = ""
    evidence: str = ""   # what matched, for explainability
    method: str = Method.TECH_RULE

    def to_dict(self):
        return {"name": self.name, "source": self.source,
                "evidence": self.evidence, "method": self.method}


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
class Signals:
    hiring: bool = False
    funding: bool = False
    ai: bool = False
    matched_snippets: list = field(default_factory=list)

    def to_dict(self):
        return {
            "hiring": self.hiring,
            "funding": self.funding,
            "ai": self.ai,
            "matched_snippets": self.matched_snippets,
        }


@dataclass
class EnrichmentResult:
    website: str = ""
    # Scalar fields carry their own provenance via Field.
    company_name: Field = field(default_factory=Field)
    description: Field = field(default_factory=Field)
    logo: Field = field(default_factory=Field)
    industry: Field = field(default_factory=Field)
    industry_confidence: float = 0.0
    employees: Field = field(default_factory=Field)   # bucket, e.g. "11-50"

    emails: list = field(default_factory=list)        # list[Email]
    phones: list = field(default_factory=list)        # list[Phone]
    addresses: list = field(default_factory=list)     # list[Address]
    social_profiles: dict = field(default_factory=dict)  # network -> SocialProfile
    technologies: list = field(default_factory=list)  # list[Technology]
    contacts: list = field(default_factory=list)      # list[Contact]
    signals: Signals = field(default_factory=Signals)

    # Diagnostics — not part of the required schema but invaluable for debugging.
    pages_crawled: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    notes: list = field(default_factory=list)   # human-readable warnings

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
            "employees": self.employees.to_dict(),
            "emails": [e.to_dict() for e in self.emails],
            "phones": [p.to_dict() for p in self.phones],
            "addresses": [a.to_dict() for a in self.addresses],
            "social_profiles": {k: v.to_dict() for k, v in self.social_profiles.items()},
            "technologies": [t.to_dict() for t in self.technologies],
            "contacts": [c.to_dict() for c in self.contacts],
            "signals": self.signals.to_dict(),
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
            "employees": self.employees.value,
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
