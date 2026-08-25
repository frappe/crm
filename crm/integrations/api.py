import ipaddress
import socket
from urllib.parse import urlparse, urlunparse

import frappe
import requests
from frappe import _
from frappe.query_builder import Order
from pypika.functions import Replace
from werkzeug.wrappers import Response

from crm.utils import are_same_phone_number, parse_phone_number


def _get_recording_credentials(telephony_medium: str) -> tuple | None:
	"""Return (api_key, secret) for the given telephony medium, or None when the
	recording needs no auth.

	A manual/unrecognized medium (a recording added by hand) is fetched as-is, and
	a provider whose credentials aren't configured yet falls back to no auth rather
	than raising — so the proxy attempts the fetch and lets the provider decide,
	instead of 500-ing before the request is even made.
	"""
	if telephony_medium == "Twilio":
		s = frappe.get_single("CRM Twilio Settings")
		secret = s.get_password("api_secret", raise_exception=False)
		return (s.api_key, secret) if s.api_key and secret else None
	elif telephony_medium == "Exotel":
		s = frappe.get_single("CRM Exotel Settings")
		token = s.get_password("api_token", raise_exception=False)
		return (s.api_key, token) if s.api_key and token else None
	# manual or unrecognized medium: no provider auth to apply
	return None


@frappe.whitelist()
def is_call_integration_enabled():
	return {
		"integrations": {
			"twilio": bool(frappe.db.get_single_value("CRM Twilio Settings", "enabled")),
			"exotel": bool(frappe.db.get_single_value("CRM Exotel Settings", "enabled")),
		},
		"default_calling_medium": get_user_default_calling_medium(),
	}


def get_user_default_calling_medium():
	if not frappe.db.exists("CRM Telephony Agent", frappe.session.user):
		return None

	default_medium = frappe.db.get_value("CRM Telephony Agent", frappe.session.user, "default_medium")

	if not default_medium:
		return None

	return default_medium


@frappe.whitelist()
def set_default_calling_medium(medium: str):
	if not frappe.db.exists("CRM Telephony Agent", frappe.session.user):
		frappe.get_doc(
			{
				"doctype": "CRM Telephony Agent",
				"user": frappe.session.user,
				"default_medium": medium,
			}
		).insert(ignore_permissions=True)
	else:
		frappe.db.set_value("CRM Telephony Agent", frappe.session.user, "default_medium", medium)

	return get_user_default_calling_medium()


@frappe.whitelist()
def add_note_to_call_log(call_sid: str, note: dict):
	"""Add/Update note to call log based on call sid."""
	if not frappe.has_permission("CRM Call Log", "write", call_sid):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	_note = None
	if not note.get("name"):
		_note = frappe.get_doc(
			{
				"doctype": "FCRM Note",
				"title": note.get("title", "Call Note"),
				"content": note.get("content"),
			}
		).insert(ignore_permissions=True)
	else:
		_note = frappe.set_value("FCRM Note", note.get("name"), "content", note.get("content"))

	call_log = frappe.get_cached_doc("CRM Call Log", call_sid)
	call_log.link_with_reference_doc("FCRM Note", _note.name)
	call_log.save(ignore_permissions=True)

	return _note


@frappe.whitelist()
def add_task_to_call_log(call_sid: str, task: dict):
	"""Add/Update task to call log based on call sid."""
	if not frappe.has_permission("CRM Call Log", "write", call_sid):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	_task = None
	if not task.get("name"):
		_task = frappe.get_doc(
			{
				"doctype": "CRM Task",
				"title": task.get("title"),
				"description": task.get("description"),
				"assigned_to": task.get("assigned_to"),
				"due_date": task.get("due_date"),
				"status": task.get("status"),
				"priority": task.get("priority"),
			}
		).insert(ignore_permissions=True)
	else:
		_task = frappe.get_doc("CRM Task", task.get("name"))
		_task.update(
			{
				"title": task.get("title"),
				"description": task.get("description"),
				"assigned_to": task.get("assigned_to"),
				"due_date": task.get("due_date"),
				"status": task.get("status"),
				"priority": task.get("priority"),
			}
		)
		_task.save(ignore_permissions=True)

	call_log = frappe.get_doc("CRM Call Log", call_sid)
	call_log.link_with_reference_doc("CRM Task", _task.name)
	call_log.save(ignore_permissions=True)

	return _task


@frappe.whitelist()
def get_contact_lead_or_deal_from_number(number: str):
	"""Get contact, lead or deal from the given number."""
	contact = get_contact_by_phone_number(number)
	if contact.get("name"):
		doctype = "Contact"
		docname = contact.get("name")
		if contact.get("lead"):
			doctype = "CRM Lead"
			docname = contact.get("lead")
		elif contact.get("deal"):
			doctype = "CRM Deal"
			docname = contact.get("deal")
		return docname, doctype
	return None, None


@frappe.whitelist()
def get_contact_by_phone_number(phone_number: str):
	"""Get contact by phone number."""
	number = parse_phone_number(phone_number)

	if number.get("is_valid"):
		return get_contact(number.get("national_number"), number.get("country"))
	else:
		return get_contact(phone_number, number.get("country"), exact_match=True)


def _resolve_validated_ip(hostname: str, port: int) -> str:
	# Refuse any host that resolves to a non-public address (cloud metadata, localhost,
	# private/link-local ranges) and return a single validated IP to connect to. Returning
	# the exact resolved IP — rather than re-resolving at connect time — is what closes the
	# DNS-rebinding TOCTOU window.
	try:
		addrinfos = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
	except socket.gaierror:
		frappe.throw(_("Invalid recording URL"), frappe.ValidationError)

	ips = [info[4][0] for info in addrinfos]
	if not ips:
		frappe.throw(_("Invalid recording URL"), frappe.ValidationError)

	for ip in ips:
		if not ipaddress.ip_address(ip).is_global:
			frappe.throw(_("Recording URL is not allowed"), frappe.ValidationError)

	return ips[0]


class _PinnedIPAdapter(requests.adapters.HTTPAdapter):
	# Connect to a pre-validated IP while keeping the original hostname for the Host header,
	# TLS SNI and certificate verification. The socket therefore reaches the exact IP that was
	# checked, so DNS can't be rebound to an internal address between check and connect.
	def __init__(self, pinned_ip: str, hostname: str, **kwargs):
		self._pinned_ip = pinned_ip
		self._hostname = hostname
		super().__init__(**kwargs)

	def send(self, request, **kwargs):
		parsed = urlparse(request.url)
		literal_ip = (
			f"[{self._pinned_ip}]" if ipaddress.ip_address(self._pinned_ip).version == 6 else self._pinned_ip
		)
		netloc = f"{literal_ip}:{parsed.port}" if parsed.port else literal_ip
		request.url = urlunparse(parsed._replace(netloc=netloc))
		host = f"[{parsed.hostname}]" if ":" in parsed.hostname else parsed.hostname
		request.headers["Host"] = f"{host}:{parsed.port}" if parsed.port else host
		if parsed.scheme == "https":
			self.poolmanager.connection_pool_kw["server_hostname"] = self._hostname
			self.poolmanager.connection_pool_kw["assert_hostname"] = self._hostname
		return super().send(request, **kwargs)


def _safe_get(url: str, auth, headers: dict):
	# TODO: this SSRF-safe fetch (host validation + IP pinning) will likely need to be shared
	# with domain enrichment; until that feature ships, this local helper is the interim workaround.
	parsed = urlparse(url)
	if parsed.scheme not in ("http", "https") or not parsed.hostname:
		frappe.throw(_("Invalid recording URL"), frappe.ValidationError)

	port = parsed.port or (443 if parsed.scheme == "https" else 80)
	pinned_ip = _resolve_validated_ip(parsed.hostname, port)

	session = requests.Session()
	session.mount(f"{parsed.scheme}://", _PinnedIPAdapter(pinned_ip, parsed.hostname))
	resp = session.get(url, auth=auth, headers=headers, stream=True, timeout=30, allow_redirects=False)
	return resp, session


def _fetch_recording(url: str, auth, headers: dict):
	# Follow redirects manually so every hop is validated and IP-pinned: a provider URL can
	# 302 to a signed CDN URL (legitimate), but without per-hop checks a redirect to an
	# internal address would bypass validation. Provider credentials are dropped after the
	# first hop so they aren't leaked to the redirect target.
	current_url = url
	current_auth = auth
	for _hop in range(5):
		resp, session = _safe_get(current_url, current_auth, headers)
		if resp.is_redirect and resp.headers.get("Location"):
			current_url = requests.compat.urljoin(current_url, resp.headers["Location"])
			current_auth = None
			resp.close()
			session.close()
			continue
		resp._pinned_session = session
		return resp

	frappe.throw(_("Too many redirects while fetching recording"), frappe.ValidationError)


@frappe.whitelist()
def get_recording_url(call_log_name: str):
	"""Proxy a call recording (authenticating with the provider) so it plays in the browser.

	Forwards the browser's Range request to the provider and passes the response back with
	Accept-Ranges/Content-Length set. Without range support the HTML <audio> element can't
	read the recording's duration (shows 0:00) or seek within it.
	"""
	if not call_log_name or not frappe.db.exists("CRM Call Log", call_log_name):
		frappe.throw(_("Call log not found"), frappe.DoesNotExistError)

	log = frappe.get_doc("CRM Call Log", call_log_name)
	log.check_permission("read")

	if not log.recording_url:
		frappe.throw(_("Recording URL not found"), frappe.DoesNotExistError)

	auth = _get_recording_credentials(log.telephony_medium)
	# forward the browser's Range header so the provider (Twilio/Exotel CDN) can return
	# just the requested bytes; falls back to the full file if it doesn't support ranges
	req_headers = {}
	range_header = frappe.get_request_header("Range")
	if range_header:
		req_headers["Range"] = range_header

	# stream instead of buffering the whole file: the provider's Content-Length reaches
	# the browser immediately so the <audio> element can show the duration right away,
	# rather than waiting for the entire recording to download server-side first
	upstream = _fetch_recording(log.recording_url, auth, req_headers)
	upstream.raise_for_status()

	def _stream():
		try:
			yield from upstream.iter_content(chunk_size=64 * 1024)
		finally:
			upstream.close()
			session = getattr(upstream, "_pinned_session", None)
			if session is not None:
				session.close()

	response = Response(
		_stream(),
		status=upstream.status_code,
		mimetype=upstream.headers.get("Content-Type") or "audio/mpeg",
	)
	response.headers["Accept-Ranges"] = "bytes"
	for header in ("Content-Length", "Content-Range"):
		if upstream.headers.get(header):
			response.headers[header] = upstream.headers[header]
	return response


def get_contact(phone_number: str, country: str = "IN", exact_match: bool = False):
	if not phone_number:
		return {"mobile_no": phone_number}

	cleaned_number = (
		phone_number.strip()
		.replace(" ", "")
		.replace("-", "")
		.replace("(", "")
		.replace(")", "")
		.replace("+", "")
	)

	# Check if the number is associated with a contact.
	# Search all of a contact's numbers (phone_nos child table) and not just the
	# primary mobile_no, so calls from a secondary number still resolve.
	Contact = frappe.qb.DocType("Contact")
	ContactPhone = frappe.qb.DocType("Contact Phone")
	normalized_phone = Replace(
		Replace(Replace(Replace(Replace(ContactPhone.phone, " ", ""), "-", ""), "(", ""), ")", ""), "+", ""
	)

	query = (
		frappe.qb.from_(ContactPhone)
		.join(Contact)
		.on(ContactPhone.parent == Contact.name)
		.select(
			Contact.name,
			Contact.full_name,
			Contact.image,
			Contact.mobile_no,
			ContactPhone.phone.as_("matched_phone"),
		)
		.where(ContactPhone.parenttype == "Contact")
		.where(normalized_phone.like(f"%{cleaned_number}%"))
		.orderby(Contact.modified, order=Order.desc)
	)
	contacts = query.run(as_dict=True)

	if len(contacts):
		# Check if the contact is associated with a deal
		for contact in contacts:
			if frappe.db.exists("CRM Contacts", {"contact": contact.name, "is_primary": 1}):
				deal = frappe.db.get_value(
					"CRM Contacts", {"contact": contact.name, "is_primary": 1}, "parent"
				)
				if are_same_phone_number(
					contact.matched_phone, phone_number, country, validate=not exact_match
				):
					contact["deal"] = deal
					return contact

	# Else, Check if the number is associated with a lead
	Lead = frappe.qb.DocType("CRM Lead")
	normalized_phone = Replace(
		Replace(Replace(Replace(Replace(Lead.mobile_no, " ", ""), "-", ""), "(", ""), ")", ""), "+", ""
	)

	query = (
		frappe.qb.from_(Lead)
		.select(Lead.name, Lead.lead_name, Lead.image, Lead.mobile_no)
		.where(Lead.converted == 0)
		.where(normalized_phone.like(f"%{cleaned_number}%"))
		.orderby("modified", order=Order.desc)
	)
	leads = query.run(as_dict=True)

	if len(leads):
		for lead in leads:
			if are_same_phone_number(lead.mobile_no, phone_number, country, validate=not exact_match):
				lead["lead"] = lead.name
				lead["full_name"] = lead.lead_name
				return lead

	if len(contacts) and are_same_phone_number(
		contacts[0].matched_phone, phone_number, country, validate=not exact_match
	):
		return contacts[0]

	return {"mobile_no": phone_number}
