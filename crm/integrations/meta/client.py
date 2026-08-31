# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Thin Meta Graph API client used by the Lead Ads integration.

Every call carries `appsecret_proof` (HMAC-SHA256 of the token with the app
secret) so the app can run with "Require app secret" enabled — a Meta
production hardening recommendation.
"""

import hashlib
import hmac

import frappe
import requests
from frappe import _

GRAPH_BASE = "https://graph.facebook.com"
GRAPH_VERSION = "v23.0"
TIMEOUT = 30


class MetaAPIError(Exception):
	def __init__(self, message, code=None, subcode=None, http_status=None):
		super().__init__(message)
		self.code = code
		self.subcode = subcode
		self.http_status = http_status


def get_settings():
	return frappe.get_cached_doc("CRM Meta Settings")


def graph_url(endpoint: str) -> str:
	return f"{GRAPH_BASE}/{GRAPH_VERSION}/{endpoint.lstrip('/')}"


def appsecret_proof(token: str) -> str | None:
	secret = get_settings().get_password("app_secret", raise_exception=False)
	if not secret:
		return None
	return hmac.new(secret.encode(), token.encode(), hashlib.sha256).hexdigest()


def graph_request(method: str, endpoint: str, token: str, params: dict | None = None) -> dict:
	params = dict(params or {})
	if token:
		params["access_token"] = token
		proof = appsecret_proof(token)
		if proof:
			params["appsecret_proof"] = proof
	try:
		response = requests.request(method, graph_url(endpoint), params=params, timeout=TIMEOUT)
	except requests.RequestException as exc:
		raise MetaAPIError(_("Network error talking to Meta: {0}").format(exc)) from exc

	try:
		data = response.json()
	except ValueError:
		data = {}
	if response.status_code >= 400 or "error" in data:
		error = data.get("error") or {}
		raise MetaAPIError(
			error.get("message") or f"HTTP {response.status_code}",
			code=error.get("code"),
			subcode=error.get("error_subcode"),
			http_status=response.status_code,
		)
	return data


def graph_get(endpoint: str, token: str, params: dict | None = None) -> dict:
	return graph_request("GET", endpoint, token, params)


def graph_post(endpoint: str, token: str, params: dict | None = None) -> dict:
	return graph_request("POST", endpoint, token, params)


def graph_get_paginated(endpoint: str, token: str, params: dict | None = None, max_pages: int = 50):
	"""Iterate all rows following paging.next (Graph caps page size; never trust
	a single call to return everything)."""
	params = dict(params or {})
	params.setdefault("limit", 100)
	url_params = params
	next_url = None
	for _page in range(max_pages):
		if next_url:
			# next_url already carries access_token + appsecret_proof + cursor
			try:
				response = requests.get(next_url, timeout=TIMEOUT)
				data = response.json()
			except (requests.RequestException, ValueError) as exc:
				raise MetaAPIError(_("Network error talking to Meta: {0}").format(exc)) from exc
			if response.status_code >= 400 or "error" in data:
				error = data.get("error") or {}
				raise MetaAPIError(error.get("message") or "pagination error", code=error.get("code"))
		else:
			data = graph_get(endpoint, token, url_params)
		yield from data.get("data", [])
		next_url = (data.get("paging") or {}).get("next")
		if not next_url:
			return


# --- token machinery -------------------------------------------------------


def exchange_code_for_token(code: str, redirect_uri: str) -> dict:
	settings = get_settings()
	return graph_request(
		"GET",
		"oauth/access_token",
		token="",
		params={
			"client_id": settings.app_id,
			"client_secret": settings.get_password("app_secret"),
			"redirect_uri": redirect_uri,
			"code": code,
		},
	)


def exchange_for_long_lived_token(short_token: str) -> dict:
	settings = get_settings()
	return graph_request(
		"GET",
		"oauth/access_token",
		token="",
		params={
			"grant_type": "fb_exchange_token",
			"client_id": settings.app_id,
			"client_secret": settings.get_password("app_secret"),
			"fb_exchange_token": short_token,
		},
	)


def debug_token(token: str) -> dict:
	settings = get_settings()
	app_token = f"{settings.app_id}|{settings.get_password('app_secret')}"
	return graph_get("debug_token", app_token, {"input_token": token}).get("data", {})
