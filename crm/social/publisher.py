# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Social publishing — directly to Meta, from Frappe.

There is exactly one publishing path: the Meta Graph API, using the page
tokens obtained by the Meta connection (Settings → Meta). No third-party
service is involved.

- Facebook Page: /feed (text), /photos (image), /videos (video)
- Instagram Business: /media (container) → wait for processing → /media_publish
  (Instagram always requires a media file; videos are published as Reels)
"""

import time

import frappe
from frappe import _
from frappe.utils import get_url

VIDEO_EXTENSIONS = (".mp4", ".mov", ".m4v")


class PublishError(Exception):
	pass


def publish_target(post, target) -> str:
	"""Publish one post to one profile; returns the provider post id."""
	from crm.integrations.meta.client import MetaAPIError, graph_post

	content = target.override_content or post.content
	media_url = get_url(post.media) if post.media else None

	account = frappe.get_doc("CRM Social Account", target.account)
	page_id = account.facebook_page or account.provider_account_id
	token = page_id and frappe.get_doc("Facebook Page", page_id).get_password(
		"access_token", raise_exception=False
	)
	if not token:
		raise PublishError(_("No Facebook page token for this profile — reconnect Facebook in Settings"))

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

		ig_id = account.provider_account_id
		if not ig_id:
			raise PublishError(_("No Instagram account id — re-import profiles in Settings"))
		if not media_url:
			raise PublishError(_("Instagram requires an image or a video"))
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
	"""Instagram processes uploads asynchronously: publish only once FINISHED."""
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
