"""Read CRM SES Settings and prime the devsecops runtime config cache.

The devsecops send stack reads `get_ses_runtime_config()` which caches an
AwsSesRuntimeConfig in `frappe.local.flags`. By calling `prime_ses_config()`
once per request (via `before_request` hook) we ensure the CRM-owned doctype
drives the send stack instead of the devsecops doctype.
"""
from __future__ import annotations

import frappe
from frappe.utils import cint, cstr

_CACHE_KEY = "aws_ses_runtime_config_v1"


def prime_ses_config() -> None:
	"""Populate the devsecops per-request config cache from CRM SES Settings."""
	try:
		from frappe_devsecops_dashboard.email.aws_ses_config import AwsSesRuntimeConfig
	except ImportError:
		return

	try:
		doc = frappe.get_cached_doc("CRM SES Settings", "CRM SES Settings")
	except Exception:
		return

	enabled = bool(cint(doc.get("enabled")))

	use_explicit = bool(cint(doc.get("use_explicit_credentials")))
	access_key_id = ""
	secret_access_key = ""
	session_token = ""
	if use_explicit:
		access_key_id = cstr(doc.get("access_key_id") or "").strip()
		secret_access_key = cstr(
			doc.get_password("secret_access_key", raise_exception=False) or ""
		).strip()
		session_token = cstr(
			doc.get_password("session_token", raise_exception=False) or ""
		).strip()

	retry_mode = cstr(doc.get("retry_mode") or "standard").strip().lower()
	if retry_mode not in {"standard", "adaptive", "legacy"}:
		retry_mode = "standard"

	total_max_attempts = cint(doc.get("total_max_attempts")) or 8
	if total_max_attempts < 1:
		total_max_attempts = 8

	sender_mode = cstr(doc.get("sender_mode") or "user_first").strip().lower()
	if sender_mode not in {"user_first", "static"}:
		sender_mode = "user_first"

	config = AwsSesRuntimeConfig(
		enabled=enabled,
		aws_region=cstr(doc.get("aws_region")).strip(),
		default_sender_email=cstr(doc.get("default_sender_email")).strip(),
		default_sender_name=cstr(doc.get("default_sender_name")).strip(),
		sender_mode=sender_mode,
		configuration_set_name=cstr(doc.get("configuration_set_name")).strip(),
		endpoint_url="",
		profile_name="",
		retry_mode=retry_mode,
		total_max_attempts=total_max_attempts,
		use_explicit_credentials=use_explicit,
		access_key_id=access_key_id,
		secret_access_key=secret_access_key,
		session_token=session_token,
	)

	frappe.local.flags[_CACHE_KEY] = config
