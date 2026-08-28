"""Expose the Domain Enrichment fields on existing sites.

The enrichment fields (company_description, linkedin, twitter, facebook) were added
to the default Lead/Deal/Organization layouts in ``crm/install.py``, but that seeder
is skip-if-exists -- so sites installed before this feature never get them and users
can't see what enrichment writes. This patch injects any missing enrichment field
into the relevant Side Panel / Data Fields / Quick Entry layouts (the Lead/Deal/
Organization Quick Entry layouts are what the create-modal quick-enrich prefill
fills). Idempotent: a field already present anywhere in the layout (or absent from
the doctype) is left untouched.
"""

import json

import frappe

ENRICHMENT_FIELDS = ["company_description", "linkedin", "twitter", "facebook"]

TARGET_LAYOUTS = [
	"CRM Lead-Side Panel",
	"CRM Deal-Side Panel",
	"CRM Organization-Side Panel",
	"CRM Lead-Data Fields",
	"CRM Deal-Data Fields",
	# Quick Entry = the create-modal layout; enrichment prefill must be visible there.
	"CRM Lead-Quick Entry",
	"CRM Deal-Quick Entry",
	"CRM Organization-Quick Entry",
]


def _iter_columns(layout):
	"""Yield every column dict in a layout tree (handles tabbed layouts that nest
	sections under a top-level section's ``sections`` key)."""
	for section in layout:
		yield from section.get("columns", [])
		for nested in section.get("sections", []):
			yield from nested.get("columns", [])


def _visible_columns(layout):
	"""Columns of the first non-hidden section (handles tabbed layouts). Skipping
	hidden sections matters for Quick Entry, whose first section (organization) is
	hidden -- fields must land in a section the user can actually see."""
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
		meta = frappe.get_meta(doc.dt)
		missing = [f for f in ENRICHMENT_FIELDS if f not in present and meta.has_field(f)]
		if not missing:
			continue

		target = _visible_columns(layout)
		if not target:
			continue

		target[0].setdefault("fields", []).extend(missing)
		doc.layout = json.dumps(layout)
		doc.save()
