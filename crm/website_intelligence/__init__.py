"""Website Intelligence — rule-based, public-data company enrichment.

This subpackage is intentionally free of any Frappe imports so it can run as a
standalone script (`python enrich.py https://example.com`) and be unit-tested
in isolation. The Frappe integration layer lives in `crm/api/website_intelligence.py`
and imports from here.

No third-party enrichment providers, no paid APIs, no LLMs are used. Everything
is derived from the target site's own HTML, JSON-LD, and meta tags via requests +
BeautifulSoup, regex, and deterministic heuristics. Every extracted value carries
the source page it came from so results are explainable.
"""

from .pipeline import enrich, WebsiteIntelligencePipeline  # noqa: F401
from .models import EnrichmentResult  # noqa: F401

__all__ = ["enrich", "WebsiteIntelligencePipeline", "EnrichmentResult"]
