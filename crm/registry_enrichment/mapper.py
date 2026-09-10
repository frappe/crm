# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Apply a ``RegistryResult`` to a CRM document.

Two write policies are supported: **Fill if empty** (write only when the target is
blank) and **Always refresh** (overwrite with a fresh non-empty value, but never clear a
stored value to empty). This module is self-contained: it does not import private
helpers from the domain module, so the two features can evolve independently. It adds
the registry-specific parts: resolving a value from the flat ``RegistryResult`` bag,
reading mappings from ``CRM Registry Enrichment Field Mapping``, materializing a Frappe
``Address`` for the structured ``address`` source key, and a small permission-respecting
link-master creator for opt-in ``create_missing_link`` mappings.
"""

from __future__ import annotations

import frappe
from frappe import _

# Write-policy constants (must match the CRM Registry Enrichment Field Mapping Select).
POLICY_FILL_IF_EMPTY = "Fill if empty"
POLICY_ALWAYS_REFRESH = "Always refresh"


def _ensure_link_target(target_doctype: str, target_fieldname: str, value: str):
	"""For a Link field with ``create_missing_link`` set, auto-create the linked master
	if it is missing. Explicit and opt-in, and permission-respecting: the master is
	created only if the enriching user could create it themselves (no
	``ignore_permissions`` escalation from registry data).

	Returns the value to write (the linked name) or ``None`` to skip the field -- when
	the master is missing and the user lacks create rights, or on any error (the field
	is skipped, the run is not aborted).
	"""
	meta = frappe.get_meta(target_doctype)
	df = meta.get_field(target_fieldname)
	if not df or df.fieldtype != "Link" or not df.options:
		# Not a Link (or unknown field) -- nothing to create; write as-is.
		return value
	link_doctype = df.options
	# Resolve against the stored name so a differently-cased master (the CNAE section
	# label "Technology" vs an existing "technology") reuses the canonical name instead
	# of writing a case-divergent value. The name match is case-insensitive under the
	# default collation, and get_value returns the master's real name.
	existing = frappe.db.get_value(link_doctype, value, "name")
	if existing:
		return existing
	# The worker runs as the user who triggered enrichment, so a user who cannot create
	# the master must not be able to insert one via registry data. Skip the field rather
	# than write a dangling link.
	if not frappe.has_permission(link_doctype, ptype="create"):
		return None
	try:
		link_meta = frappe.get_meta(link_doctype)
		new_doc = {"doctype": link_doctype}
		# Populate the field the master autonames from (e.g. CRM Industry.industry),
		# falling back to the title field, so the created record's name == value.
		autoname = link_meta.autoname or ""
		if autoname.startswith("field:"):
			new_doc[autoname.split(":", 1)[1]] = value
		elif link_meta.get_title_field():
			new_doc[link_meta.get_title_field()] = value
		else:
			new_doc["__newname"] = value
		# Permission-respecting insert -- the create right was checked above.
		frappe.get_doc(new_doc).insert()
		return value
	except Exception:
		frappe.log_error(
			title="Registry Enrichment: could not create link master",
			message=f"{link_doctype}={value!r} for {target_doctype}.{target_fieldname}",
		)
		return None


# Human labels for the realtime "filled: ..." toast, built at call time so ``_()``
# resolves in the requesting user's language (a module-level dict would cache one).
def _source_key_labels() -> dict:
	return {
		"legal_name": _("Legal Name"),
		"trade_name": _("Trade Name"),
		"tax_id": _("Tax ID"),
		"registration_status": _("Registration Status"),
		"registration_status_date": _("Registration Status Date"),
		"opening_date": _("Opening Date"),
		"legal_nature": _("Legal Nature"),
		"company_size": _("Company Size"),
		"share_capital": _("Share Capital"),
		"tax_regime": _("Tax Regime"),
		"simples_nacional": _("Simples Nacional"),
		"industry": _("Industry"),
		"industry_section": _("Industry"),
		"email": _("Email"),
		"phone": _("Phone"),
		"mobile_no": _("Mobile"),
		"address": _("Address"),
	}


def _label_for(doc, source_key: str, target_fieldname: str) -> str:
	label = _source_key_labels().get(source_key)
	if label:
		return label
	df = doc.meta.get_field(target_fieldname)
	return df.label if df and df.label else target_fieldname


def _find_or_create_address(doc, address: dict) -> str | None:
	"""Return the name of an ``Address`` for ``doc``, creating it if missing.

	Deduplicates on ``address_title`` + ``pincode`` so re-enriching the same record
	does not spawn a second Address. Creation is permission-respecting: a user who
	cannot create an Address gets ``None`` (the field is skipped, the run is not
	aborted) rather than an ``ignore_permissions`` escalation from registry data.
	"""
	title = doc.get("organization_name") or doc.get("lead_name") or doc.name
	pincode = address.get("pincode") or ""

	existing = frappe.db.get_value("Address", {"address_title": title, "pincode": pincode})
	if existing:
		return existing

	if not frappe.has_permission("Address", ptype="create"):
		return None

	try:
		new_address = frappe.new_doc("Address")
		new_address.address_title = title
		new_address.address_type = "Billing"
		for key in ("address_line1", "address_line2", "city", "state", "pincode", "country"):
			if address.get(key):
				new_address.set(key, address[key])
		new_address.append("links", {"link_doctype": doc.doctype, "link_name": doc.name})
		new_address.insert()
		return new_address.name
	except Exception:
		frappe.log_error(
			title="Registry Enrichment: could not create Address",
			message=f"{doc.doctype}={doc.name}",
		)
		return None


def _apply_address(doc, result, mapping) -> bool:
	"""Fill the Address link field from ``result.address`` under the mapping policy.

	Only the Fill-if-empty and Always-refresh policies are meaningful for a Link; the
	Address is materialized then linked. Returns True when the field was set.
	"""
	fieldname = mapping.target_fieldname
	if not result.address:
		return False
	current = doc.get(fieldname)
	policy = mapping.write_policy or POLICY_FILL_IF_EMPTY
	if current and policy != POLICY_ALWAYS_REFRESH:
		return False

	name = _find_or_create_address(doc, result.address)
	if not name or current == name:
		return False
	doc.set(fieldname, name)
	return True


def apply_to_document(doc, result, mappings) -> list[str]:
	"""Populate mappable fields on a Lead / Organization from ``result``.

	For each enabled mapping the value is resolved by ``source_key`` from the flat
	``RegistryResult`` bag and written per ``write_policy``:

	* **Fill if empty** -- set only when the target field is currently empty.
	* **Always refresh** -- overwrite with a fresh non-empty value; never clears a
	  stored value to empty (enrichment must not destroy data).

	Does NOT save the document. Returns the human labels of the fields changed.
	"""
	filled: list[str] = []

	for mapping in mappings:
		fieldname = mapping.target_fieldname
		if not doc.meta.has_field(fieldname):
			continue

		label = _label_for(doc, mapping.source_key, fieldname)

		if mapping.source_key == "address":
			if _apply_address(doc, result, mapping) and label not in filled:
				filled.append(label)
			continue

		value = result.get(mapping.source_key)
		if value in (None, ""):
			continue

		current = doc.get(fieldname)
		policy = mapping.write_policy or POLICY_FILL_IF_EMPTY

		if policy == POLICY_ALWAYS_REFRESH:
			if current == value:
				continue
		else:  # Fill if empty
			if current or current == value:
				continue

		if mapping.create_missing_link:
			value = _ensure_link_target(doc.doctype, fieldname, value)
			if value is None:
				continue

		doc.set(fieldname, value)
		if label not in filled:
			filled.append(label)

	return filled
