#!/usr/bin/env python3
"""Standalone CLI for Website Intelligence.

Usage:
    python enrich.py https://frappe.io
    python enrich.py https://frappe.io --max-pages 8 --depth 2 --quiet

Prints the canonical enrichment JSON to stdout. Progress is written to stderr so
stdout stays valid JSON for piping (e.g. `python enrich.py URL | jq`).

Works with no Frappe environment: it adds the parent dir to sys.path so the
`website_intelligence` package imports cleanly whether run from inside the bench
or copied out as a standalone folder.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

# Allow running directly: `python enrich.py URL` from inside the package dir.
if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from website_intelligence.pipeline import WebsiteIntelligencePipeline, PROGRESS_STEPS
else:  # imported as a module
    from .pipeline import WebsiteIntelligencePipeline, PROGRESS_STEPS


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Enrich a company from its public website (no external APIs).")
    parser.add_argument("website", help="Company website URL, e.g. https://frappe.io")
    parser.add_argument("--max-pages", type=int, default=10,
                        help="Maximum pages to crawl (default 10)")
    parser.add_argument("--depth", type=int, default=2,
                        help="Maximum crawl depth (default 2)")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress progress output on stderr")
    parser.add_argument("--indent", type=int, default=2,
                        help="JSON indent (default 2)")
    args = parser.parse_args(argv)

    def progress(step_index, message):
        if not args.quiet:
            print(f"[{step_index + 1}/{len(PROGRESS_STEPS)}] {message}",
                  file=sys.stderr, flush=True)

    try:
        pipeline = WebsiteIntelligencePipeline(
            args.website, max_pages=args.max_pages, max_depth=args.depth,
            progress=progress)
        result = pipeline.run()
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stdout)
        return 2

    print(json.dumps(result.to_dict(), indent=args.indent, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
