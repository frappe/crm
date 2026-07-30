from __future__ import annotations

import frappe
from frappe import _


@frappe.whitelist()
def get_settings() -> dict:
	"""Return public-safe SES settings for the frontend config UI.
	Secrets (access_key_id, secret_access_key, session_token) are never returned.
	"""
	_require_manager()
	try:
		doc = frappe.get_cached_doc("AWS SES Settings", "AWS SES Settings")
	except frappe.DoesNotExistError:
		return {}
	return {
		"enabled": bool(doc.get("enabled")),
		"aws_region": doc.get("aws_region") or "",
		"default_sender_email": doc.get("default_sender_email") or "",
		"default_sender_name": doc.get("default_sender_name") or "",
		"sender_mode": doc.get("sender_mode") or "user_first",
		"configuration_set_name": doc.get("configuration_set_name") or "",
		"retry_mode": doc.get("retry_mode") or "standard",
		"total_max_attempts": doc.get("total_max_attempts") or 8,
		"use_explicit_credentials": bool(doc.get("use_explicit_credentials")),
		"has_access_key": bool(doc.get_password("secret_access_key", raise_exception=False)),
	}


@frappe.whitelist(methods=["POST"])
def update_settings(settings: dict) -> dict:
	"""Persist non-secret SES settings. Secrets are managed via Frappe desk."""
	_require_manager()
	ALLOWED = {
		"enabled",
		"aws_region",
		"default_sender_email",
		"default_sender_name",
		"sender_mode",
		"configuration_set_name",
		"retry_mode",
		"total_max_attempts",
		"use_explicit_credentials",
	}
	try:
		doc = frappe.get_doc("AWS SES Settings", "AWS SES Settings")
	except frappe.DoesNotExistError:
		frappe.throw(
			_(
				"AWS SES Settings not found. Ensure frappe_devsecops_dashboard is installed."
			)
		)

	for key, value in settings.items():
		if key in ALLOWED:
			doc.set(key, value)

	doc.save(ignore_permissions=True)  # SYSTEM-INTERNAL: settings are manager-gated above
	frappe.clear_cache(doctype="AWS SES Settings")

	try:
		from frappe_devsecops_dashboard.email.aws_ses_config import clear_ses_runtime_config_cache
		clear_ses_runtime_config_cache()
	except ImportError:
		pass

	return get_settings()


def _require_manager() -> None:
	user = frappe.session.user
	if user == "Administrator":
		return
	roles = frappe.get_roles(user)
	if "System Manager" not in roles and "Sales Manager" not in roles:
		frappe.throw(_("Only CRM Managers can modify SES settings."), frappe.PermissionError)
