from __future__ import annotations

import frappe
from frappe import _


@frappe.whitelist()
def get_settings() -> dict:
	"""Return public-safe SES + inbound settings for the frontend config UI.
	Secrets (access_key_id, secret_access_key, session_token) are never returned.
	"""
	_require_manager()
	try:
		doc = frappe.get_cached_doc("AWS SES Settings", "AWS SES Settings")
	except frappe.DoesNotExistError:
		return {}

	fcrm = frappe.get_cached_doc("FCRM Settings", "FCRM Settings")
	inbound_account_name = fcrm.get("inbound_email_account") or ""

	inbound = _get_inbound_account_fields(inbound_account_name)

	return {
		# Outbound / transport
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
		# Inbound
		"inbound_email_account": inbound_account_name,
		"enable_incoming": inbound.get("enable_incoming", False),
		"default_incoming": inbound.get("default_incoming", False),
		"append_to": inbound.get("append_to", ""),
		"create_lead_from_incoming_email": inbound.get("create_lead_from_incoming_email", False),
	}


def _get_inbound_account_fields(account_name: str) -> dict:
	if not account_name:
		return {}
	try:
		ea = frappe.get_cached_doc("Email Account", account_name)
		return {
			"enable_incoming": bool(ea.get("enable_incoming")),
			"default_incoming": bool(ea.get("default_incoming")),
			"append_to": ea.get("append_to") or "",
			"create_lead_from_incoming_email": bool(ea.get("create_lead_from_incoming_email")),
		}
	except frappe.DoesNotExistError:
		return {}


@frappe.whitelist(methods=["POST"])
def update_settings(settings: dict) -> dict:
	"""Persist non-secret SES settings and inbound Email Account fields."""
	_require_manager()

	SES_ALLOWED = {
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
	FCRM_ALLOWED = {"inbound_email_account"}
	EMAIL_ACCOUNT_ALLOWED = {
		"enable_incoming",
		"default_incoming",
		"append_to",
		"create_lead_from_incoming_email",
	}

	try:
		ses_doc = frappe.get_doc("AWS SES Settings", "AWS SES Settings")
	except frappe.DoesNotExistError:
		frappe.throw(
			_("AWS SES Settings not found. Ensure frappe_devsecops_dashboard is installed.")
		)

	for key, value in settings.items():
		if key in SES_ALLOWED:
			ses_doc.set(key, value)
	ses_doc.save(ignore_permissions=True)  # SYSTEM-INTERNAL: settings are manager-gated above
	frappe.clear_cache(doctype="AWS SES Settings")

	# Persist inbound_email_account pointer to FCRM Settings
	fcrm_dirty = {k: v for k, v in settings.items() if k in FCRM_ALLOWED}
	if fcrm_dirty:
		fcrm = frappe.get_doc("FCRM Settings", "FCRM Settings")
		for key, value in fcrm_dirty.items():
			fcrm.set(key, value)
		fcrm.save(ignore_permissions=True)  # SYSTEM-INTERNAL: settings are manager-gated above
		frappe.clear_cache(doctype="FCRM Settings")

	# Persist inbound fields directly on the Email Account document
	ea_dirty = {k: v for k, v in settings.items() if k in EMAIL_ACCOUNT_ALLOWED}
	if ea_dirty:
		account_name = settings.get("inbound_email_account") or (
			frappe.db.get_single_value("FCRM Settings", "inbound_email_account") or ""
		)
		if account_name and frappe.db.exists("Email Account", account_name):
			ea = frappe.get_doc("Email Account", account_name)
			for key, value in ea_dirty.items():
				ea.set(key, value)
			ea.save(ignore_permissions=True)  # SYSTEM-INTERNAL: settings are manager-gated above
			frappe.clear_cache(doctype="Email Account")

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
