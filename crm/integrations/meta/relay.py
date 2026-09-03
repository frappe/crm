# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Hub-side routing for a Meta app shared by many client sites.

Webhook subscriptions are configured per APP, not per page, so an agency app
serving one Frappe site per client has a single callback URL for everybody.
The site behind that URL is the hub: it keeps a page → site table and forwards
each leadgen notification to the CRM that owns the page.

Both directions are authenticated with `meta_relay_secret`, shared by every
site of the bench through common_site_config.json:

- client → hub: `register_page_route`, signed with page id + site + timestamp
- hub → client: `X-CRM-Relay-Signature`, an HMAC of the forwarded body
"""

import hashlib
import hmac
import json
import time

import frappe
import requests
from frappe.utils import get_url
from werkzeug.wrappers import Response

TIMEOUT = 15
MAX_SKEW = 300


def relay_secret() -> str:
	return frappe.conf.get("meta_relay_secret") or ""


def sign(message: bytes) -> str:
	return hmac.new(relay_secret().encode(), message, hashlib.sha256).hexdigest()


def valid_relay_signature(header: str | None, raw_body: bytes) -> bool:
	if not relay_secret() or not header:
		return False
	return hmac.compare_digest(header, sign(raw_body))


def route_for(page_id: str) -> str | None:
	"""Site that owns this page, or None when it is not routed elsewhere."""
	if not page_id:
		return None
	site = frappe.db.get_value("Meta Page Route", page_id, "site_url")
	if not site or site.rstrip("/") == get_url().rstrip("/"):
		return None
	return site.rstrip("/")


def forward(site: str, payload: dict) -> None:
	"""Deliver one page's notification to the client site that owns it."""
	body = json.dumps(payload).encode()
	try:
		response = requests.post(
			f"{site}/api/method/crm.integrations.meta.webhook.handle",
			data=body,
			headers={
				"Content-Type": "application/json",
				"X-CRM-Relay-Signature": sign(body),
			},
			timeout=TIMEOUT,
		)
		if response.status_code >= 300:
			raise ValueError(f"HTTP {response.status_code}: {response.text[:200]}")
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"Meta relay: forward to {site} failed")
		return
	frappe.db.set_value(
		"Meta Page Route",
		{"site_url": site},
		"last_forwarded_at",
		frappe.utils.now_datetime(),
		update_modified=False,
	)


@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
def register_page_route(page_id: str, site: str, ts: str, signature: str):
	"""Client site → hub: 'leads for this page belong to me'.

	Called whenever a client enables lead sync for a page. Authenticated with
	the shared relay secret, so only sites of our own bench can claim a page.
	"""
	if not relay_secret():
		return Response("relay not configured", status=400, mimetype="text/plain")
	if abs(int(time.time()) - int(ts or 0)) > MAX_SKEW:
		return Response("stale request", status=403, mimetype="text/plain")
	expected = sign(f"{page_id}|{site}|{ts}".encode())
	if not hmac.compare_digest(signature or "", expected):
		return Response("invalid signature", status=403, mimetype="text/plain")

	site = site.rstrip("/")
	if frappe.db.exists("Meta Page Route", page_id):
		frappe.db.set_value("Meta Page Route", page_id, "site_url", site)
	else:
		frappe.get_doc({"doctype": "Meta Page Route", "page_id": page_id, "site_url": site}).insert(
			ignore_permissions=True
		)
	frappe.db.commit()
	return Response("ok", mimetype="text/plain")


def claim_page(page_id: str) -> None:
	"""Register this site as the owner of a page on the hub (best effort)."""
	from crm.integrations.meta.oauth import hub_url

	hub = hub_url()
	if not hub or not relay_secret():
		return
	site = get_url().rstrip("/")
	ts = str(int(time.time()))
	try:
		requests.post(
			f"{hub}/api/method/crm.integrations.meta.relay.register_page_route",
			json={
				"page_id": page_id,
				"site": site,
				"ts": ts,
				"signature": sign(f"{page_id}|{site}|{ts}".encode()),
			},
			timeout=TIMEOUT,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Meta relay: could not claim page on the hub")
