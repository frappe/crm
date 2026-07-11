"""Expose the Domain Enrichment fields on existing sites.

The enrichment fields (company_description, linkedin, twitter, facebook) were added
to the default Lead/Deal/Organization layouts in ``crm/install.py``, but that seeder
is skip-if-exists -- so sites installed before this feature never get them and users
can't see what enrichment writes. This patch injects any missing enrichment field
into the relevant Side Panel / Data Fields layouts. Idempotent: a field already
present anywhere in the layout (or absent from the doctype) is left untouched.
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
]


def _iter_columns(layout):
	"""Yield every column dict in a layout tree (handles tabbed layouts that nest
	sections under a top-level section's ``sections`` key)."""
	for section in layout:
		yield from section.get("columns", [])
		for nested in section.get("sections", []):
			yield from nested.get("columns", [])


def execute():
	for name in TARGET_LAYOUTS:
		if not frappe.db.exists("CRM Fields Layout", name):
			continue

		doc = frappe.get_doc("CRM Fields Layout", name)
		try:
			layout = json.loads(doc.layout or "[]")
		except (ValueError, TypeError):
			continue

		columns = list(_iter_columns(layout))
		if not columns:
			continue

		present = {f for col in columns for f in col.get("fields", [])}
		meta = frappe.get_meta(doc.dt)
		missing = [f for f in ENRICHMENT_FIELDS if f not in present and meta.has_field(f)]
		if not missing:
			continue

		columns[0].setdefault("fields", []).extend(missing)
		doc.layout = json.dumps(layout)
		doc.save()
