import frappe
from frappe.tests import IntegrationTestCase

from crm.api.doc import get_data


def lead_names(filters):
	result = get_data(
		doctype="CRM Lead",
		filters=filters,
		order_by="modified desc",
		page_length=100,
		view={"view_type": "list"},
	)
	return [row["name"] for row in result["data"]]


class TestCommentsFilter(IntegrationTestCase):
	"""The Comments filter must search the full comment text, not the `_comments`
	cache that Frappe truncates to ~100 characters."""

	def setUp(self):
		frappe.set_user("Administrator")
		self.marker = frappe.generate_hash(length=10)
		self.matching = self.make_lead("Match")
		self.other = self.make_lead("Other")
		self.add_comment(self.matching, f"{'x' * 150} deep text {self.marker}")
		self.add_comment(self.other, "A short unrelated comment")

	def tearDown(self):
		frappe.db.rollback()

	def make_lead(self, first_name):
		return frappe.get_doc({"doctype": "CRM Lead", "first_name": first_name}).insert().name

	def add_comment(self, lead, content, comment_type="Comment"):
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": comment_type,
				"reference_doctype": "CRM Lead",
				"reference_name": lead,
				"content": content,
			}
		).insert(ignore_permissions=True)

	def test_like_matches_text_past_the_truncated_cache(self):
		names = lead_names({"_comments": ["like", f"%deep text {self.marker}%"]})

		self.assertIn(self.matching, names)
		self.assertNotIn(self.other, names)

	def test_not_like_excludes_leads_with_matching_comment(self):
		names = lead_names({"_comments": ["not like", f"%{self.marker}%"]})

		self.assertNotIn(self.matching, names)
		self.assertIn(self.other, names)

	def test_like_combines_with_other_filters(self):
		filters = {"_comments": ["like", f"%{self.marker}%"]}

		self.assertEqual(lead_names({**filters, "name": self.matching}), [self.matching])
		self.assertEqual(lead_names({**filters, "name": self.other}), [])

	def test_only_comments_of_type_comment_are_searched(self):
		self.add_comment(self.other, f"info {self.marker}", comment_type="Info")

		names = lead_names({"_comments": ["like", f"%info {self.marker}%"]})

		self.assertNotIn(self.other, names)
