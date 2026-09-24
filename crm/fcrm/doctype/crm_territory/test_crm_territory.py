# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import UnitTestCase
from frappe.utils.nestedset import get_descendants_of

TERRITORIES = ("_Test Territory Grandchild", "_Test Territory Child", "_Test Territory Parent")
CYCLIC = ("_Test Cyclic A", "_Test Cyclic B", "_Test Cyclic Self")


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

		# inserted below the ORM, so clear them the same way
		frappe.db.delete("CRM Territory", {"name": ["in", CYCLIC]})

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

	def test_patch_breaks_legacy_parent_cycles(self):
		"""Territories on a parent cycle predate any validation.

		`rebuild_tree` only walks down from roots, so it never reaches them and they
		silently keep lft/rgt at 0, which hides them from every tree filter.
		"""
		insert_legacy_territory("_Test Cyclic A", parent="_Test Cyclic B")
		insert_legacy_territory("_Test Cyclic B", parent="_Test Cyclic A")
		insert_legacy_territory("_Test Cyclic Self", parent="_Test Cyclic Self")

		execute_rebuild_patch()

		for name in CYCLIC:
			lft, rgt = frappe.db.get_value("CRM Territory", name, ["lft", "rgt"])
			self.assertGreater(lft, 0, f"{name} was left outside the tree")
			self.assertGreater(rgt, lft, f"{name} has invalid boundaries")

		# exactly one link per cycle is cleared, so the rest of the chain is preserved
		self.assertIsNone(frappe.db.get_value("CRM Territory", "_Test Cyclic Self", "parent_crm_territory"))
		remaining = [
			name
			for name in ("_Test Cyclic A", "_Test Cyclic B")
			if frappe.db.get_value("CRM Territory", name, "parent_crm_territory")
		]
		self.assertEqual(len(remaining), 1)

	def test_patch_leaves_valid_tree_untouched(self):
		execute_rebuild_patch()

		self.parent.reload()
		self.child.reload()
		self.assertEqual(
			frappe.db.get_value("CRM Territory", self.child.name, "parent_crm_territory"),
			self.parent.name,
		)
		self.assertGreater(self.child.lft, self.parent.lft)
		self.assertLess(self.child.rgt, self.parent.rgt)


def execute_rebuild_patch():
	from crm.patches.v1_0.rebuild_crm_territory_tree import execute

	execute()


def insert_legacy_territory(name, parent=None):
	"""Insert a row the way it could exist before the controller used NestedSet:
	no validation, and lft/rgt never computed."""
	frappe.db.sql(
		"""insert into `tabCRM Territory`
			(name, territory_name, parent_crm_territory, is_group, lft, rgt,
			 owner, modified_by, creation, modified, docstatus)
		values (%s, %s, %s, 0, 0, 0, 'Administrator', 'Administrator', now(), now(), 0)""",
		(name, name, parent),
	)


def make_territory(name, parent=None, is_group=0):
	return frappe.get_doc(
		{
			"doctype": "CRM Territory",
			"territory_name": name,
			"parent_crm_territory": parent,
			"is_group": is_group,
		}
	).insert()
