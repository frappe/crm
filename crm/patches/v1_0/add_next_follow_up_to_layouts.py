"""Expose the Next Follow Up field on existing sites.

``next_follow_up`` was added to the default Lead/Deal Side Panel layouts in
``crm/install.py``, but that seeder is skip-if-exists -- so sites installed
before this feature would get the field and its reminders without anywhere to
set the date. This patch appends it to the relevant layouts.

Idempotent: a layout that already lists the field (or a doctype that doesn't
have it) is left untouched.
"""

import json

import frappe

FIELDNAME = "next_follow_up"

TARGET_LAYOUTS = [
	"CRM Lead-Side Panel",
	"CRM Deal-Side Panel",
]


def _iter_columns(layout):
	"""Yield every column dict in a layout tree (handles tabbed layouts that nest
	sections under a top-level section's ``sections`` key)."""
	for section in layout:
		yield from section.get("columns", [])
		for nested in section.get("sections", []):
			yield from nested.get("columns", [])


def _visible_columns(layout):
	"""Columns of the first non-hidden section that has any -- the field has to
	land somewhere the user can actually see it."""
	for section in layout:
		if section.get("hidden"):
			continue
		if section.get("columns"):
			return section["columns"]
		for nested in section.get("sections", []):
			if not nested.get("hidden") and nested.get("columns"):
				return nested["columns"]
	return None


def execute():
	for name in TARGET_LAYOUTS:
		if not frappe.db.exists("CRM Fields Layout", name):
			continue

		doc = frappe.get_doc("CRM Fields Layout", name)
		try:
			layout = json.loads(doc.layout or "[]")
		except (ValueError, TypeError):
			continue

		present = {f for col in _iter_columns(layout) for f in col.get("fields", [])}
		if FIELDNAME in present or not frappe.get_meta(doc.dt).has_field(FIELDNAME):
			continue

		target = _visible_columns(layout)
		if not target:
			continue

		target[0].setdefault("fields", []).append(FIELDNAME)
		doc.layout = json.dumps(layout)
		doc.save()
