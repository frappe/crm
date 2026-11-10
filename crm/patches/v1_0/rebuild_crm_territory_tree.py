import frappe
from frappe.utils.nestedset import rebuild_tree


def execute():
	"""Repair CRM Territory tree data created before the controller used NestedSet.

	Until now `lft`/`rgt` were never computed (always 0) and nothing stopped a
	leaf territory (`is_group=0`) from being assigned as a parent. Promote any
	such leaf-with-children to a group so the tree is consistent, then rebuild
	the nested set boundaries for the whole doctype.
	"""
	territory = frappe.qb.DocType("CRM Territory")
	parents_with_children = (
		frappe.qb.from_(territory)
		.select(territory.parent_crm_territory)
		.where(territory.parent_crm_territory.isnotnull() & (territory.parent_crm_territory != ""))
		.distinct()
		.run(pluck=True)
	)

	if parents_with_children:
		frappe.qb.update(territory).set(territory.is_group, 1).where(
			territory.name.isin(parents_with_children) & (territory.is_group == 0)
		).run()

	rebuild_tree("CRM Territory")
