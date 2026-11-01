import re
from collections import Counter
from pathlib import Path

from frappe.tests import UnitTestCase

from crm.fcrm.form_script_analysis import CATALOG

GUIDE = Path(__file__).parents[2] / "docs" / "form-scripts-on-desk-v2.md"
ANCHOR = re.compile(r'<a id="([^"]+)"></a>')
HEADING = re.compile(r"^#{1,6} (.+)$", re.MULTILINE)
LOCAL_LINK = re.compile(r"\]\(#([^)]+)\)")


def github_slug(heading: str) -> str:
	return re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")


class TestFormScriptGuide(UnitTestCase):
	"""The report links each v1 call to `<guide>#<catalog key>`."""

	def setUp(self):
		self.guide = GUIDE.read_text()

	def test_every_catalog_key_has_one_anchor(self):
		anchors = Counter(ANCHOR.findall(self.guide))
		self.assertEqual({key: anchors[key] for key in CATALOG if anchors[key] != 1}, {})
		self.assertEqual(set(anchors) - set(CATALOG), set())

	def test_no_heading_slug_is_a_catalog_key(self):
		# GitHub gives a heading the same `user-content-` id as an anchor, so the two would clash.
		slugs = {github_slug(heading) for heading in HEADING.findall(self.guide)}
		self.assertEqual(slugs & set(CATALOG), set())

	def test_local_links_resolve(self):
		targets = set(ANCHOR.findall(self.guide)) | {
			github_slug(heading) for heading in HEADING.findall(self.guide)
		}
		self.assertEqual(set(LOCAL_LINK.findall(self.guide)) - targets, set())
