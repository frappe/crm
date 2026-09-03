import frappe


def execute():
	"""A task should belong to at most one call log, but that rule was only enforced
	going forward once `_unlink_task_from_other_call_logs` shipped. Clean up any task
	that was already linked to more than one call log before then.

	Dynamic Link.creation can't tell us which link came first: Frappe copies a new
	child row's `creation` from its parent document's own `creation` whenever the
	parent already existed (see `set_user_and_timestamp` in frappe/model/document.py),
	so it reflects when the call happened, not when the task was linked to it. A task
	is created in the same request that links it to its originating call (see
	`add_task_to_call_log`), so the call log whose own creation is closest to the
	task's creation is the best available signal for which call the task actually
	originated from - keep that one and drop the rest."""
	duplicate_tasks = frappe.db.sql(
		"""
		SELECT link_name
		FROM `tabDynamic Link`
		WHERE parenttype = 'CRM Call Log'
			AND link_doctype = 'CRM Task'
		GROUP BY link_name
		HAVING COUNT(*) > 1
		""",
		as_dict=True,
	)

	for row in duplicate_tasks:
		task_creation = frappe.db.get_value("CRM Task", row.link_name, "creation")
		if not task_creation:
			continue

		links = frappe.db.get_all(
			"Dynamic Link",
			filters={
				"parenttype": "CRM Call Log",
				"link_doctype": "CRM Task",
				"link_name": row.link_name,
			},
			fields=["name", "parent"],
		)

		call_log_creations = frappe.db.get_all(
			"CRM Call Log",
			filters={"name": ("in", [link.parent for link in links])},
			fields=["name", "creation"],
		)
		creation_by_call_log = {c.name: c.creation for c in call_log_creations}

		links.sort(key=lambda link: abs(creation_by_call_log[link.parent] - task_creation))

		for link in links[1:]:
			frappe.db.delete("Dynamic Link", {"name": link.name})
