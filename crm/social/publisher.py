# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Pluggable social publishing adapters.

The Social Planner UI/doctypes are provider-agnostic; publishing goes through
one of these adapters, chosen in CRM Social Settings:

- Postiz  — self-hosted open-source engine, public REST API
            (https://docs.postiz.com/public-api). One agency-level instance,
            per-network OAuth handled by Postiz.
- Ayrshare — paid aggregator (https://www.ayrshare.com), zero app reviews:
            fastest path to real publishing.
- Manual  — no external call: the post is marked published and the team posts
            it by hand (also useful for testing the planner itself).
"""

import datetime

import frappe
import requests
from frappe import _
from frappe.utils import get_url

TIMEOUT = 30


class PublishError(Exception):
	pass


def get_settings():
	return frappe.get_cached_doc("CRM Social Settings")


def publish_target(post, target) -> str:
	"""Publish one post to one account; returns the provider post id."""
	settings = get_settings()
	provider = settings.provider or "Manual"
	content = target.override_content or post.content
	media_url = get_url(post.media) if post.media else None
	if provider == "Postiz":
		return _publish_postiz(settings, target, content, media_url, post)
	if provider == "Ayrshare":
		return _publish_ayrshare(settings, target, content, media_url, post)
	return "manual"


def _publish_postiz(settings, target, content, media_url, post) -> str:
	base = (settings.postiz_url or "").rstrip("/")
	api_key = settings.get_password("postiz_api_key", raise_exception=False)
	if not base or not api_key:
		raise PublishError(_("Postiz URL/API key not configured"))
	if not target.get("provider_account_id"):
		raise PublishError(_("Account has no Postiz integration id"))

	headers = {"Authorization": api_key, "Content-Type": "application/json"}
	value = [{"content": content}]
	if media_url:
		value[0]["image"] = [{"path": media_url}]
	body = {
		"type": "now",
		"date": datetime.datetime.utcnow().isoformat() + "Z",
		"posts": [
			{
				"integration": {"id": target.provider_account_id},
				"value": value,
			}
		],
	}
	response = requests.post(f"{base}/public/v1/posts", json=body, headers=headers, timeout=TIMEOUT)
	if response.status_code >= 300:
		raise PublishError(f"Postiz {response.status_code}: {response.text[:300]}")
	data = response.json() if response.text else {}
	if isinstance(data, list) and data:
		return str(data[0].get("postId") or data[0].get("id") or "ok")
	return str(data.get("id") or "ok") if isinstance(data, dict) else "ok"


AYRSHARE_PLATFORMS = {
	"Facebook": "facebook",
	"Instagram": "instagram",
	"LinkedIn": "linkedin",
	"TikTok": "tiktok",
	"YouTube": "youtube",
	"Pinterest": "pinterest",
	"Google Business Profile": "gmb",
	"Threads": "threads",
	"Bluesky": "bluesky",
	"X": "twitter",
}


def _publish_ayrshare(settings, target, content, media_url, post) -> str:
	api_key = settings.get_password("ayrshare_api_key", raise_exception=False)
	if not api_key:
		raise PublishError(_("Ayrshare API key not configured"))
	platform = AYRSHARE_PLATFORMS.get(target.get("platform"))
	if not platform:
		raise PublishError(_("Platform not supported by Ayrshare: {0}").format(target.get("platform")))

	body = {"post": content, "platforms": [platform]}
	if media_url:
		body["mediaUrls"] = [media_url]
	if target.get("provider_account_id"):
		body["profileKey"] = target.provider_account_id
	response = requests.post(
		"https://app.ayrshare.com/api/post",
		json=body,
		headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
		timeout=TIMEOUT,
	)
	data = response.json() if response.text else {}
	if response.status_code >= 300 or data.get("status") == "error":
		raise PublishError(f"Ayrshare {response.status_code}: {str(data)[:300]}")
	return str(data.get("id") or "ok")


# ---------------------------------------------------------------------------
# scheduler
# ---------------------------------------------------------------------------


def process_due_posts() -> None:
	"""Every few minutes: publish scheduled posts whose time has come."""
	due = frappe.get_all(
		"CRM Social Post",
		filters={"status": "Scheduled", "scheduled_at": ["<=", frappe.utils.now_datetime()]},
		pluck="name",
		limit=50,
	)
	for name in due:
		try:
			publish_post(name)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), f"Social Planner: publish failed ({name})")


def publish_post(name: str) -> None:
	post = frappe.get_doc("CRM Social Post", name)
	if post.status != "Scheduled":
		return
	any_failed = False
	for target in post.targets:
		if target.status == "Published":
			continue
		try:
			target.provider_post_id = publish_target(post, target)
			target.status = "Published"
			target.error = ""
		except Exception as exc:
			any_failed = True
			target.status = "Failed"
			target.error = str(exc)[:400]
			frappe.log_error(frappe.get_traceback(), f"Social Planner: target failed ({name})")

	post.status = "Failed" if any_failed else "Published"
	if post.status == "Published":
		post.published_at = frappe.utils.now_datetime()
		schedule_recurrence(post)
	post.save(ignore_permissions=True)
	frappe.publish_realtime("crm_social_post", {"name": post.name, "status": post.status})


def schedule_recurrence(post) -> None:
	if (post.recurrence or "None") == "None" or not post.scheduled_at:
		return
	delta = {"Daily": {"days": 1}, "Weekly": {"days": 7}, "Monthly": {"months": 1}}[post.recurrence]
	next_post = frappe.copy_doc(post)
	next_post.status = "Scheduled"
	next_post.published_at = None
	next_post.scheduled_at = frappe.utils.add_to_date(post.scheduled_at, **delta)
	for target in next_post.targets:
		target.status = "Pending"
		target.provider_post_id = ""
		target.error = ""
	next_post.insert(ignore_permissions=True)
