import frappe
from frappe.tests.utils import FrappeTestCase

from crm.api.doc import get_data, get_filterable_fields


def make_territory(name, parent=None, is_group=0):
	return frappe.get_doc(
		{
			"doctype": "CRM Territory",
			"territory_name": name,
			"parent_crm_territory": parent,
			"is_group": is_group,
		}
	).insert(ignore_permissions=True)


class TestListTreeFilter(FrappeTestCase):
	"""Filtering leads by a parent territory must also match its child
	territories (#2209)."""

	def setUp(self):
		frappe.set_user("Administrator")
		make_territory("_Test 2209 India", is_group=1)
		make_territory("_Test 2209 Assam", parent="_Test 2209 India", is_group=1)
		make_territory("_Test 2209 Nagaon", parent="_Test 2209 Assam")
		make_territory("_Test 2209 Marigaon", parent="_Test 2209 Assam")
		make_territory("_Test 2209 Kerala", parent="_Test 2209 India")

		self.leads = {}
		for territory in (
			"_Test 2209 Assam",
			"_Test 2209 Nagaon",
			"_Test 2209 Marigaon",
			"_Test 2209 Kerala",
		):
			lead = frappe.get_doc(
				{"doctype": "CRM Lead", "first_name": "Tree Filter", "territory": territory}
			).insert(ignore_permissions=True)
			self.leads[lead.name] = territory

	def tearDown(self):
		frappe.db.rollback()

	def territories_matching(self, territory_filter):
		result = get_data(
			doctype="CRM Lead",
			filters={"name": ["in", list(self.leads)], "territory": territory_filter},
			order_by="modified desc",
			rows=["name", "territory"],
			columns=[],
			view={"view_type": "list"},
		)
		return sorted(row["territory"] for row in result["data"])

	def test_territory_is_flagged_as_tree(self):
		fields = {field["fieldname"]: field for field in get_filterable_fields("CRM Lead")}

		self.assertTrue(fields["territory"]["is_tree"])
		self.assertFalse(fields["lead_owner"]["is_tree"])
		self.assertFalse(fields["first_name"]["is_tree"])

	def test_descendants_inclusive_matches_parent_and_children(self):
		self.assertEqual(
			self.territories_matching(["descendants of (inclusive)", "_Test 2209 Assam"]),
			["_Test 2209 Assam", "_Test 2209 Marigaon", "_Test 2209 Nagaon"],
		)

	def test_descendants_inclusive_spans_multiple_levels(self):
		self.assertEqual(
			self.territories_matching(["descendants of (inclusive)", "_Test 2209 India"]),
			["_Test 2209 Assam", "_Test 2209 Kerala", "_Test 2209 Marigaon", "_Test 2209 Nagaon"],
		)

	def test_equals_still_matches_only_that_territory(self):
		self.assertEqual(self.territories_matching("_Test 2209 Assam"), ["_Test 2209 Assam"])
