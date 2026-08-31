import json

import frappe
from frappe import _

MANAGER_ROLES = {"System Manager", "Sales Manager"}


def _is_manager() -> bool:
	return bool(MANAGER_ROLES & set(frappe.get_roles()))


def _check_manager():
	if not _is_manager():
		frappe.throw(_("Only sales managers can do this"), frappe.PermissionError)


@frappe.whitelist()
def get_accounts() -> list[dict]:
	return frappe.get_list(
		"CRM Social Account",
		filters={"enabled": 1},
		fields=["name", "account_name", "platform", "provider_account_id"],
		order_by="platform asc",
	)


@frappe.whitelist()
def get_posts(start: str, end: str) -> list[dict]:
	"""Posts in a date range (calendar view) plus undated drafts."""
	posts = frappe.get_list(
		"CRM Social Post",
		filters={"scheduled_at": ["between", [start, end]]},
		fields=["name", "status", "scheduled_at", "published_at", "content", "media", "recurrence"],
		order_by="scheduled_at asc",
		page_length=500,
	)
	drafts = frappe.get_list(
		"CRM Social Post",
		filters={"scheduled_at": ["is", "not set"], "status": ["in", ["Draft", "Pending Approval"]]},
		fields=["name", "status", "scheduled_at", "published_at", "content", "media", "recurrence"],
		page_length=100,
	)
	rows = posts + drafts
	targets = frappe.get_all(
		"CRM Social Post Target",
		filters={"parent": ["in", [r.name for r in rows]]},
		fields=["parent", "account", "platform", "status", "error", "override_content"],
	)
	by_post: dict[str, list] = {}
	for t in targets:
		by_post.setdefault(t.parent, []).append(t)
	for row in rows:
		row["targets"] = by_post.get(row.name, [])
	return rows


@frappe.whitelist(methods=["POST"])
def save_post(post: dict | str, name: str | None = None) -> dict:
	if isinstance(post, str):
		post = json.loads(post)

	targets = post.get("targets") or []
	if not targets:
		frappe.throw(_("Select at least one social account"))
	values = {
		"content": (post.get("content") or "").strip(),
		"scheduled_at": post.get("scheduled_at") or None,
		"media": post.get("media") or "",
		"recurrence": post.get("recurrence") or "None",
		"targets": [
			{
				"account": t.get("account"),
				"override_content": t.get("override_content") or "",
				"status": "Pending",
			}
			for t in targets
		],
	}
	if not values["content"]:
		frappe.throw(_("Content is required"))

	requested_status = post.get("status") or "Draft"
	if requested_status in ("Scheduled", "Published") and not _is_manager():
		requested_status = "Pending Approval"
	if requested_status == "Scheduled" and not values["scheduled_at"]:
		frappe.throw(_("Pick a date and time to schedule"))

	if name:
		doc = frappe.get_doc("CRM Social Post", name)
		if doc.status == "Published":
			frappe.throw(_("Published posts cannot be edited"))
		doc.update(values)
	else:
		doc = frappe.get_doc({"doctype": "CRM Social Post", **values})

	doc.status = requested_status
	if requested_status == "Pending Approval":
		doc.requested_by = frappe.session.user
	if requested_status == "Scheduled":
		doc.approved_by = frappe.session.user
	doc.save() if name else doc.insert()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist(methods=["POST"])
def approve_post(name: str) -> dict:
	_check_manager()
	doc = frappe.get_doc("CRM Social Post", name)
	if doc.status != "Pending Approval":
		frappe.throw(_("Post is not pending approval"))
	if not doc.scheduled_at:
		frappe.throw(_("Set a schedule date before approving"))
	doc.status = "Scheduled"
	doc.approved_by = frappe.session.user
	doc.save()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist(methods=["POST"])
def publish_now(name: str) -> dict:
	_check_manager()
	doc = frappe.get_doc("CRM Social Post", name)
	if doc.status in ("Published",):
		frappe.throw(_("Already published"))
	doc.status = "Scheduled"
	doc.scheduled_at = doc.scheduled_at or frappe.utils.now_datetime()
	doc.approved_by = frappe.session.user
	doc.save()
	from crm.social.publisher import publish_post

	publish_post(doc.name)
	doc.reload()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist(methods=["POST"])
def cancel_post(name: str) -> dict:
	doc = frappe.get_doc("CRM Social Post", name)
	if doc.status == "Published":
		frappe.throw(_("Already published"))
	if not _is_manager() and doc.owner != frappe.session.user:
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	doc.status = "Cancelled"
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def get_provider() -> dict:
	settings = frappe.get_cached_doc("CRM Social Settings")
	return {"provider": settings.provider or "Manual"}
