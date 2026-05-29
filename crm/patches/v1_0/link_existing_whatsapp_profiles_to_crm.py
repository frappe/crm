# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe

from crm.integrations.api import get_all_matches_by_phone_number


def execute():
	"""Link existing WhatsApp Profile records to matching CRM entities.

	This is a one-time migration for profiles created before the auto-linking
	feature was added. It uses the same logic as _link_profile_to_crm_entities()
	in crm.api.whatsapp.

	Idempotent: safe to run multiple times.
	"""
	if not frappe.db.exists("DocType", "WhatsApp Profile"):
		return

	profiles = frappe.get_all(
		"WhatsApp Profile",
		filters={"phone_number": ["!=", ""]},
		fields=["name", "phone_number"],
	)

	if not profiles:
		return

	for profile_row in profiles:
		try:
			_link_single_profile(profile_row.name, profile_row.phone_number)
		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				f"Migration: failed to link WhatsApp Profile {profile_row.name}",
			)


def _link_single_profile(profile_name: str, phone_number: str):
	"""Link a single WhatsApp Profile to matching CRM entities."""
	if not phone_number:
		return

	matches = get_all_matches_by_phone_number(phone_number)
	if not matches:
		return

	profile = frappe.get_doc("WhatsApp Profile", profile_name)

	existing_links = {(link.link_doctype, link.link_name) for link in (profile.links or [])}

	needs_save = False
	for match in matches:
		doctype = match["doctype"]
		docname = match["docname"]
		key = (doctype, docname)

		if key not in existing_links:
			profile.append(
				"links",
				{
					"link_doctype": doctype,
					"link_name": docname,
					"link_title": docname,
				},
			)
			needs_save = True

	if needs_save:
		profile.flags.ignore_permissions = True
		profile.save(ignore_permissions=True)
		frappe.db.commit()
