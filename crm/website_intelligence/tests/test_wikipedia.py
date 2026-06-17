"""Wikipedia description lookup — match logic tested with a fake HTTP session
(no network). The real network path is exercised manually."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from website_intelligence import wikipedia  # noqa: E402


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class _FakeSession:
    """Returns canned search/Wikidata responses keyed by the API base URL."""

    def __init__(self, search_payload, wikidata_payload):
        self.search_payload = search_payload
        self.wikidata_payload = wikidata_payload

    def get(self, url, params=None, timeout=None):
        if url == wikipedia.WIKIDATA_API:
            return _FakeResp(self.wikidata_payload)
        return _FakeResp(self.search_payload)


def _search(extract="The New York Times is an American daily newspaper.", qid="Q9684"):
    return {"query": {"pages": {"123": {
        "index": 1, "pageid": 123, "extract": extract,
        "pageprops": {"wikibase_item": qid},
    }}}}


def _wikidata(site="https://www.nytimes.com/"):
    return {"claims": {"P856": [
        {"mainsnak": {"datavalue": {"value": site}}}
    ]}}


class WikipediaTest(unittest.TestCase):
    def test_uses_extract_when_domain_matches(self):
        session = _FakeSession(_search(), _wikidata("https://www.nytimes.com/"))
        text, source = wikipedia.fetch_company_description(
            "The New York Times", "https://www.nytimes.com", session=session)
        self.assertTrue(text.startswith("The New York Times is"))
        self.assertIn("wikipedia.org", source)

    def test_rejected_when_domain_mismatch(self):
        # Same-named page but its official site is a different company → skip.
        session = _FakeSession(_search(), _wikidata("https://someoneelse.com/"))
        text, source = wikipedia.fetch_company_description(
            "The New York Times", "https://www.nytimes.com", session=session)
        self.assertEqual(text, "")
        self.assertEqual(source, "")

    def test_blank_inputs_short_circuit(self):
        self.assertEqual(
            wikipedia.fetch_company_description("", "https://x.com"), ("", ""))
        self.assertEqual(
            wikipedia.fetch_company_description("X", ""), ("", ""))

    def test_network_error_returns_empty(self):
        class Boom:
            def get(self, *a, **k):
                raise RuntimeError("offline")
        self.assertEqual(
            wikipedia.fetch_company_description("X", "https://x.com", session=Boom()),
            ("", ""))

    def test_trim_keeps_it_short(self):
        long = "A. " + ("word " * 200)
        self.assertLessEqual(len(wikipedia._trim(long)), wikipedia.MAX_CHARS)

    def test_registrable_domain(self):
        self.assertEqual(
            wikipedia._registrable_domain("https://www.nytimes.com/section"),
            "nytimes.com")


if __name__ == "__main__":
    unittest.main()
