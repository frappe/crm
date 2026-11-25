#!/usr/bin/env python3
"""Stamp unreleased "What's new" entries in frontend/src/changelog/ with a version and date.

Usage: stamp_changelog.py <version> <date>
"""

import re
import sys
from pathlib import Path

CHANGELOG_DIR = Path(__file__).resolve().parents[2] / "frontend" / "src" / "changelog"
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
UNRELEASED = re.compile(r"^version:\s*unreleased\s*$", re.MULTILINE)
DATE_LINE = re.compile(r"^date:.*$", re.MULTILINE)


def stamp(source: str, version: str, date: str) -> str | None:
	"""Return the entry with version and date set, or None if it is already released."""
	frontmatter = FRONTMATTER.match(source)
	if not frontmatter or not UNRELEASED.search(frontmatter.group(1)):
		return None

	fields = UNRELEASED.sub(f"version: {version}", frontmatter.group(1))
	if DATE_LINE.search(fields):
		fields = DATE_LINE.sub(f"date: {date}", fields)
	else:
		fields += f"\ndate: {date}"
	return f"---\n{fields}\n---\n" + source[frontmatter.end() :]


if __name__ == "__main__":
	_, version, date = sys.argv
	for path in sorted(CHANGELOG_DIR.glob("*.md")):
		stamped = stamp(path.read_text(), version, date)
		if stamped is not None:
			path.write_text(stamped)
			print(path.relative_to(CHANGELOG_DIR.parents[2]))
