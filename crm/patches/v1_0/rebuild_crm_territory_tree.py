import frappe
from frappe.utils.nestedset import rebuild_tree


def execute():
	"""Repair CRM Territory tree data created before the controller used NestedSet.

	Until now `lft`/`rgt` were never computed (always 0) and nothing stopped a
	leaf territory (`is_group=0`) from being assigned as a parent, or a territory
	from being linked into a parent cycle (including being its own parent).

	`rebuild_tree` only walks down from roots, so any territory sitting on a cycle
	is never visited and silently keeps `lft`/`rgt` at 0, which leaves it invisible
	to every tree filter. Break those cycles first, then promote leaf-with-children
	to a group, and only then rebuild the nested set boundaries.
	"""
	break_parent_cycles()

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


def break_parent_cycles():
	"""Detach every territory that sits on a parent cycle, making it a root.

	The territory and its children are kept; only the link that closes the cycle is
	cleared, so an admin can re-parent it correctly afterwards.
	"""
	territory = frappe.qb.DocType("CRM Territory")
	parent_of = dict(frappe.qb.from_(territory).select(territory.name, territory.parent_crm_territory).run())

	detached = []
	# `state` marks a node as being walked (1) or already known-acyclic (2), so each
	# node is visited once across all walks.
	state = {}

	for start in parent_of:
		if state.get(start):
			continue

		path = []
		node = start
		while node and node in parent_of and state.get(node) != 2:
			if state.get(node) == 1:
				# walked into a node from this same walk -> `node` closes a cycle
				parent_of[node] = None
				detached.append(node)
				break
			state[node] = 1
			path.append(node)
			node = parent_of.get(node)

		for visited in path:
			state[visited] = 2

	if not detached:
		return

	frappe.qb.update(territory).set(territory.parent_crm_territory, None).where(
		territory.name.isin(detached)
	).run()

	frappe.log_error(
		title="CRM Territory: cyclic parents detached",
		message=(
			"These territories were part of a parent cycle and have been made root "
			"territories so the tree could be rebuilt. Re-parent them as needed:\n"
			+ "\n".join(sorted(detached))
		),
	)
