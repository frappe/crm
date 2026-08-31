# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Pluggable social publishing adapters.

The Social Planner UI/doctypes are provider-agnostic; publishing goes through
one of these adapters, chosen in CRM Social Settings:

- Meta    — built-in: publishes directly to Facebook Pages and their linked
            Instagram Business accounts with the Graph API, reusing the page
            tokens obtained by the Meta OAuth connection (no third party).
- Postiz  — self-hosted open-source engine, public REST API
            (https://docs.postiz.com/public-api). One agency-level instance,
            per-network OAuth handled by Postiz.
- Ayrshare — paid aggregator (https://www.ayrshare.com), zero app reviews:
            fastest path to networks Meta does not cover.
- Manual  — no external call: the post is marked published and the team posts
            it by hand (also useful for testing the planner itself).
"""

import datetime
import time

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
	if provider == "Meta":
		return _publish_meta(target, content, media_url)
	if provider == "Postiz":
		return _publish_postiz(settings, target, content, media_url, post)
	if provider == "Ayrshare":
		return _publish_ayrshare(settings, target, content, media_url, post)
	return "manual"


# --- Meta (direct Graph API) ------------------------------------------------

VIDEO_EXTENSIONS = (".mp4", ".mov", ".m4v")


def _publish_meta(target, content, media_url) -> str:
	from crm.integrations.meta.client import MetaAPIError, graph_post

	account = frappe.get_doc("CRM Social Account", target.account)
	if account.platform not in ("Facebook", "Instagram"):
		raise PublishError(
			_("The built-in Meta provider only publishes to Facebook and Instagram ({0} selected)").format(
				account.platform
			)
		)
	page_id = account.facebook_page or (account.platform == "Facebook" and account.provider_account_id)
	token = page_id and frappe.get_doc("Facebook Page", page_id).get_password(
		"access_token", raise_exception=False
	)
	if not token:
		raise PublishError(_("No Facebook page token for this account — reconnect Facebook in Settings"))

	is_video = bool(media_url) and media_url.lower().split("?")[0].endswith(VIDEO_EXTENSIONS)
	try:
		if account.platform == "Facebook":
			fb_id = account.provider_account_id or page_id
			if is_video:
				result = graph_post(f"{fb_id}/videos", token, {"file_url": media_url, "description": content})
			elif media_url:
				result = graph_post(f"{fb_id}/photos", token, {"url": media_url, "caption": content})
			else:
				result = graph_post(f"{fb_id}/feed", token, {"message": content})
			return str(result.get("id") or result.get("post_id") or "ok")

		# Instagram: create a media container, wait until processed, publish it
		ig_id = account.provider_account_id
		if not ig_id:
			raise PublishError(_("No Instagram account id — re-import accounts in Settings"))
		if not media_url:
			raise PublishError(_("Instagram requires an image or video"))
		params = (
			{"media_type": "REELS", "video_url": media_url, "caption": content}
			if is_video
			else {"image_url": media_url, "caption": content}
		)
		container = graph_post(f"{ig_id}/media", token, params)
		container_id = container.get("id")
		_wait_for_ig_container(container_id, token, tries=20 if is_video else 5)
		result = graph_post(f"{ig_id}/media_publish", token, {"creation_id": container_id})
		return str(result.get("id") or "ok")
	except MetaAPIError as exc:
		raise PublishError(f"Meta: {exc}") from exc


def _wait_for_ig_container(container_id, token, tries=10, delay=3):
	from crm.integrations.meta.client import graph_get

	for attempt in range(tries):
		status = graph_get(container_id, token, {"fields": "status_code"}).get("status_code")
		if status == "FINISHED":
			return
		if status in ("ERROR", "EXPIRED"):
			raise PublishError(_("Instagram rejected the media (container status: {0})").format(status))
		if attempt < tries - 1:
			time.sleep(delay)
	raise PublishError(_("Instagram media processing timed out — retry in a minute"))


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
