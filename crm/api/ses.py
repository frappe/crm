from __future__ import annotations

import frappe
from frappe import _

_DOCTYPE = "CRM SES Settings"

# Fields written directly on the linked Email Account
_EA_FIELDS = {"enable_incoming", "default_incoming", "append_to", "create_lead_from_incoming_email"}

# Password fields stored with Frappe's encrypted password mechanism
_PASSWORD_FIELDS = {"secret_access_key", "session_token"}

# All non-credential, non-inbound fields that live on CRM SES Settings
_SES_FIELDS = {
	"enabled",
	"aws_region",
	"default_sender_email",
	"default_sender_name",
	"configuration_set_name",
	"retry_mode",
	"total_max_attempts",
	"use_explicit_credentials",
	"access_key_id",
	"inbound_email_account",
	"enable_incoming",
	"default_incoming",
	"append_to",
	"create_lead_from_incoming_email",
}


@frappe.whitelist()
def get_settings() -> dict:
	"""Return all CRM SES Settings for the frontend. Passwords are never returned."""
	_require_manager()
	try:
		doc = frappe.get_cached_doc(_DOCTYPE, _DOCTYPE)
	except frappe.DoesNotExistError:
		return {}

	return {
		"enabled": bool(doc.get("enabled")),
		"aws_region": doc.get("aws_region") or "",
		"default_sender_email": doc.get("default_sender_email") or "",
		"default_sender_name": doc.get("default_sender_name") or "",
		"configuration_set_name": doc.get("configuration_set_name") or "",
		"retry_mode": doc.get("retry_mode") or "standard",
		"total_max_attempts": doc.get("total_max_attempts") or 8,
		"use_explicit_credentials": bool(doc.get("use_explicit_credentials")),
		"access_key_id": doc.get("access_key_id") or "",
		# passwords: return a boolean so the UI knows whether they are set
		"has_secret_access_key": bool(
			doc.get_password("secret_access_key", raise_exception=False)
		),
		"has_session_token": bool(
			doc.get_password("session_token", raise_exception=False)
		),
		# inbound
		"inbound_email_account": doc.get("inbound_email_account") or "",
		"enable_incoming": bool(doc.get("enable_incoming")),
		"default_incoming": bool(doc.get("default_incoming")),
		"append_to": doc.get("append_to") or "CRM Lead",
		"create_lead_from_incoming_email": bool(doc.get("create_lead_from_incoming_email")),
	}


@frappe.whitelist(methods=["POST"])
def update_settings(settings: dict) -> dict:
	"""Persist CRM SES Settings including credentials and inbound Email Account fields."""
	_require_manager()

	try:
		doc = frappe.get_doc(_DOCTYPE, _DOCTYPE)
	except frappe.DoesNotExistError:
		frappe.throw(_("CRM SES Settings not found. Run bench migrate."))

	for key, value in settings.items():
		if key in _SES_FIELDS and key not in _PASSWORD_FIELDS:
			doc.set(key, value)

	# Handle passwords separately: only update if a non-empty value was sent
	for pf in _PASSWORD_FIELDS:
		val = (settings.get(pf) or "").strip()
		if val:
			doc.set(pf, val)

	doc.save(ignore_permissions=True)  # SYSTEM-INTERNAL: manager check above
	frappe.clear_cache(doctype=_DOCTYPE)

	# Invalidate the per-request SES config cache so the next send uses new values
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
