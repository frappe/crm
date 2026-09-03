# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Social profiles, imported from the Meta connection.

Nothing is typed by hand: profiles come from the Facebook Pages connected in
Settings → Meta, plus the Instagram Business account linked to each page.
"""

import frappe
from frappe import _


def upsert_account(
	platform: str,
	provider_account_id: str,
	account_name: str,
	facebook_page: str | None = None,
) -> str:
	"""Create/refresh one CRM Social Account, matching by (platform, provider id).

	Returns "created" or "updated"."""
	existing = frappe.db.get_value(
		"CRM Social Account",
		{"platform": platform, "provider_account_id": provider_account_id},
		"name",
	)
	if existing:
		doc = frappe.get_doc("CRM Social Account", existing)
		doc.facebook_page = facebook_page or doc.facebook_page
		if account_name and doc.account_name != account_name:
			# account_name is the docname: rename only when it will not clash
			if not frappe.db.exists("CRM Social Account", account_name):
				frappe.rename_doc("CRM Social Account", existing, account_name, force=True)
				doc = frappe.get_doc("CRM Social Account", account_name)
				doc.facebook_page = facebook_page or doc.facebook_page
		doc.save(ignore_permissions=True)
		return "updated"

	name = account_name or f"{platform} {provider_account_id}"
	if frappe.db.exists("CRM Social Account", name):
		name = f"{name} ({platform})"
	frappe.get_doc(
		{
			"doctype": "CRM Social Account",
			"account_name": name,
			"platform": platform,
			"provider_account_id": provider_account_id,
			"facebook_page": facebook_page,
			"enabled": 1,
		}
	).insert(ignore_permissions=True)
	return "created"


def sync_from_facebook_pages() -> dict:
	"""One profile per connected Facebook Page (+ its linked Instagram account)."""
	created = updated = 0
	pages = frappe.get_all(
		"Facebook Page",
		fields=["name", "page_name", "instagram_account_id", "instagram_username"],
	)
	if not pages:
		frappe.throw(_("No Facebook pages connected yet — connect Facebook first in Settings → Meta"))
	for page in pages:
		result = upsert_account("Facebook", page.name, page.page_name or page.name, page.name)
		created += result == "created"
		updated += result == "updated"
		if page.instagram_account_id:
			ig_name = f"@{page.instagram_username}" if page.instagram_username else page.instagram_account_id
			result = upsert_account("Instagram", page.instagram_account_id, ig_name, page.name)
			created += result == "created"
			updated += result == "updated"
	return {"created": created, "updated": updated}
