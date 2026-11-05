import json

import frappe

LAYOUT = "CRM Task-Quick Entry"


def execute():
	layout = frappe.db.get_value("CRM Fields Layout", LAYOUT, "layout")
	if not layout or '"all_day"' in layout:
		return

	tabs = json.loads(layout)
	for column in _columns(tabs):
		fields = column.get("fields", [])
		if "due_date" in fields:
			fields.insert(fields.index("due_date") + 1, "all_day")
			frappe.db.set_value("CRM Fields Layout", LAYOUT, "layout", json.dumps(tabs))
			return


def _columns(tabs):
	for tab in tabs:
		# older layouts list sections at the top level, without tabs
		for section in tab.get("sections", [tab]):
			yield from section.get("columns", [])
