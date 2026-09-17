# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import UnitTestCase
from frappe.utils.nestedset import get_descendants_of

TERRITORIES = ("_Test Territory Grandchild", "_Test Territory Child", "_Test Territory Parent")


class TestCRMTerritory(UnitTestCase):
	def setUp(self):
		self.cleanup()
		self.parent = make_territory("_Test Territory Parent", is_group=1)
		self.child = make_territory("_Test Territory Child", parent=self.parent.name)

	def tearDown(self):
		self.cleanup()

	def cleanup(self):
		# delete leaves before groups; NestedSet refuses to delete a node with children
		for name in TERRITORIES:
			if frappe.db.exists("CRM Territory", name):
				frappe.delete_doc("CRM Territory", name, force=True)

	def test_lft_rgt_are_computed(self):
		self.parent.reload()
		self.child.reload()

		self.assertGreater(self.parent.lft, 0)
		self.assertGreater(self.parent.rgt, self.parent.lft)
		self.assertGreater(self.child.lft, self.parent.lft)
		self.assertLess(self.child.rgt, self.parent.rgt)

	def test_tree_filters_work(self):
		self.assertEqual(get_descendants_of("CRM Territory", self.parent.name), [self.child.name])
		self.assertEqual(
			frappe.get_all(
				"CRM Territory", filters={"name": ["descendants of", self.parent.name]}, pluck="name"
			),
			[self.child.name],
		)
		self.assertEqual(
			frappe.get_all(
				"CRM Territory", filters={"name": ["ancestors of", self.child.name]}, pluck="name"
			),
			[self.parent.name],
		)

	def test_cannot_add_child_under_leaf(self):
		self.assertRaises(
			frappe.ValidationError,
			make_territory,
			"_Test Territory Grandchild",
			parent=self.child.name,
		)

	def test_cannot_be_own_parent(self):
		self.parent.parent_crm_territory = self.parent.name
		self.assertRaises(frappe.ValidationError, self.parent.save)

	def test_cannot_convert_group_with_children_to_leaf(self):
		self.parent.is_group = 0
		self.assertRaises(frappe.ValidationError, self.parent.save)

	def test_cannot_delete_group_with_children(self):
		self.assertRaises(frappe.ValidationError, frappe.delete_doc, "CRM Territory", self.parent.name)


def make_territory(name, parent=None, is_group=0):
	return frappe.get_doc(
		{
			"doctype": "CRM Territory",
			"territory_name": name,
			"parent_crm_territory": parent,
			"is_group": is_group,
		}
	).insert()
