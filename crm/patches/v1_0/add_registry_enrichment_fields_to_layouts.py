"""Expose the Registry Enrichment fields on existing sites.

The fiscal Custom Fields (tax_id, trade_name, registration_status, ...) are created on
CRM Lead / CRM Organization by ``crm.registry_enrichment.install.seed_defaults``. This
patch first ensures those Custom Fields exist (calling the same idempotent creator the
seeder uses, so the patch does not depend on install order), then injects any missing
registry field into the relevant Side Panel / Quick Entry layouts so users can see what
enrichment writes. Idempotent throughout: Custom Fields are updated in place, and a
field already present anywhere in a layout (or absent from the doctype) is left
untouched.
"""

import json

import frappe

from crm.registry_enrichment.install import create_registry_custom_fields

REGISTRY_FIELDS = [
	"tax_id",
	"trade_name",
	"registration_status",
	"registration_status_date",
	"opening_date",
	"legal_nature",
	"company_size",
	"share_capital",
	"tax_regime",
	"simples_nacional",
]

TARGET_LAYOUTS = [
	"CRM Lead-Side Panel",
	"CRM Organization-Side Panel",
	# Quick Entry = the create-modal layout; registry fields must be visible there.
	"CRM Lead-Quick Entry",
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
	hidden sections matters for Quick Entry, whose first section is hidden -- fields
	must land in a section the user can actually see."""
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
	# Create the fiscal Custom Fields first (idempotent), so the layout injection below
	# always finds them on the doctype regardless of whether the seeder ran yet.
	create_registry_custom_fields()

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
		missing = [f for f in REGISTRY_FIELDS if f not in present and meta.has_field(f)]
		if not missing:
			continue

		target = _visible_columns(layout)
		if not target:
			continue

		target[0].setdefault("fields", []).extend(missing)
		doc.layout = json.dumps(layout)
		doc.save()
