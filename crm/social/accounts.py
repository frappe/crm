# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Auto-discovery of connectable social profiles.

Instead of typing provider ids by hand, accounts are imported from the
configured provider:

- Meta     — the Facebook Pages (and their linked Instagram Business accounts)
             already connected via the Meta OAuth flow.
- Postiz   — GET {url}/public/v1/integrations lists the channels connected in
             the Postiz UI.
- Ayrshare — GET /api/user lists the networks linked to the Ayrshare profile.
"""

import frappe
import requests
from frappe import _

TIMEOUT = 30


def get_settings():
	return frappe.get_cached_doc("CRM Social Settings")


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
	"""One CRM Social Account per connected Facebook Page (+ linked IG account)."""
	created = updated = 0
	pages = frappe.get_all(
		"Facebook Page",
		fields=["name", "page_name", "instagram_account_id", "instagram_username"],
	)
	if not pages:
		frappe.throw(_("No Facebook pages connected yet — connect Facebook first (Meta Lead Ads settings)"))
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


# Postiz integration identifiers → CRM platform names
POSTIZ_PLATFORMS = {
	"facebook": "Facebook",
	"instagram": "Instagram",
	"instagram-standalone": "Instagram",
	"linkedin": "LinkedIn",
	"linkedin-page": "LinkedIn",
	"x": "X",
	"twitter": "X",
	"tiktok": "TikTok",
	"youtube": "YouTube",
	"pinterest": "Pinterest",
	"threads": "Threads",
	"bluesky": "Bluesky",
	"gmb": "Google Business Profile",
	"google-business": "Google Business Profile",
	"google-my-business": "Google Business Profile",
}


def sync_from_postiz() -> dict:
	settings = get_settings()
	base = (settings.postiz_url or "").rstrip("/")
	api_key = settings.get_password("postiz_api_key", raise_exception=False)
	if not base or not api_key:
		frappe.throw(_("Set the Postiz URL and API key first"))

	try:
		response = requests.get(
			f"{base}/public/v1/integrations",
			headers={"Authorization": api_key},
			timeout=TIMEOUT,
		)
	except requests.RequestException as exc:
		frappe.throw(_("Could not reach Postiz: {0}").format(exc))
	if response.status_code >= 300:
		frappe.throw(_("Postiz error {0}: {1}").format(response.status_code, response.text[:200]))

	rows = response.json() or []
	created = updated = 0
	skipped = []
	for row in rows:
		platform = POSTIZ_PLATFORMS.get((row.get("identifier") or "").lower())
		if not platform or row.get("disabled"):
			if not platform:
				skipped.append(row.get("identifier"))
			continue
		result = upsert_account(platform, row.get("id"), row.get("name") or row.get("id"))
		created += result == "created"
		updated += result == "updated"
	return {"created": created, "updated": updated, "skipped": [s for s in skipped if s]}


AYRSHARE_TO_PLATFORM = {
	"facebook": "Facebook",
	"instagram": "Instagram",
	"linkedin": "LinkedIn",
	"tiktok": "TikTok",
	"youtube": "YouTube",
	"pinterest": "Pinterest",
	"gmb": "Google Business Profile",
	"threads": "Threads",
	"bluesky": "Bluesky",
	"twitter": "X",
}


def sync_from_ayrshare() -> dict:
	settings = get_settings()
	api_key = settings.get_password("ayrshare_api_key", raise_exception=False)
	if not api_key:
		frappe.throw(_("Set the Ayrshare API key first"))

	try:
		response = requests.get(
			"https://app.ayrshare.com/api/user",
			headers={"Authorization": f"Bearer {api_key}"},
			timeout=TIMEOUT,
		)
	except requests.RequestException as exc:
		frappe.throw(_("Could not reach Ayrshare: {0}").format(exc))
	data = response.json() if response.text else {}
	if response.status_code >= 300:
		frappe.throw(_("Ayrshare error {0}: {1}").format(response.status_code, str(data)[:200]))

	created = updated = 0
	for row in data.get("displayNames") or []:
		platform = AYRSHARE_TO_PLATFORM.get((row.get("platform") or "").lower())
		if not platform:
			continue
		label = row.get("displayName") or row.get("username") or platform
		# provider_account_id stays empty: Ayrshare targets by platform on the
		# default profile (profileKey is only for multi-profile Business plans)
		existing = frappe.db.get_value("CRM Social Account", {"platform": platform}, "name")
		if existing:
			doc = frappe.get_doc("CRM Social Account", existing)
			doc.enabled = 1
			doc.save(ignore_permissions=True)
			updated += 1
		else:
			name = label if not frappe.db.exists("CRM Social Account", label) else f"{label} ({platform})"
			frappe.get_doc(
				{
					"doctype": "CRM Social Account",
					"account_name": name,
					"platform": platform,
					"enabled": 1,
				}
			).insert(ignore_permissions=True)
			created += 1
	return {"created": created, "updated": updated}
