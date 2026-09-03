# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""WhatsApp connection — client-site side.

The client never sees a token: they press Connect, the hub runs Embedded Signup
(where they scan the QR code from their WhatsApp Business app), and hands the
credentials back here, signed with the relay secret. This module turns them into
a ready `WhatsApp Account` for frappe_whatsapp, which owns the messaging itself.
"""

import json

import frappe
from frappe import _
from frappe.utils import get_url
from werkzeug.wrappers import Response

from crm.integrations.meta.client import get_app_id
from crm.integrations.meta.relay import valid_relay_signature
from crm.integrations.whatsapp.signup import CONNECT_PATH, config_id, make_state

MANAGER_ROLES = {"System Manager", "Sales Manager"}


def _check_manager():
	if not MANAGER_ROLES & set(frappe.get_roles()):
		frappe.throw(_("Only sales managers can manage WhatsApp"), frappe.PermissionError)


def whatsapp_installed() -> bool:
	return (
		frappe.db.exists("DocType", "WhatsApp Account") and "frappe_whatsapp" in frappe.get_installed_apps()
	)


def hub_url() -> str:
	from crm.integrations.meta.oauth import hub_url as meta_hub

	return meta_hub() or get_url().rstrip("/")


@frappe.whitelist()
def get_status() -> dict:
	_check_manager()
	if not whatsapp_installed():
		return {"installed": False}

	accounts = frappe.get_all(
		"WhatsApp Account",
		fields=["name", "phone_id", "business_id", "status"],
		order_by="creation desc",
	)
	default = frappe.db.get_single_value("WhatsApp Settings", "default_outgoing_account")
	return {
		"installed": True,
		"can_connect": bool(get_app_id() and config_id()),
		"accounts": accounts,
		"default_account": default,
		"connected": bool(accounts),
	}


@frappe.whitelist()
def get_connect_url() -> dict:
	"""Where to send the browser to run Embedded Signup on the hub."""
	_check_manager()
	if not whatsapp_installed():
		frappe.throw(_("The WhatsApp app is not installed on this site"))
	if not config_id():
		frappe.throw(_("WhatsApp signup is not configured yet — ask your provider"))
	state = make_state(get_url().rstrip("/"))
	return {"url": f"{hub_url()}{CONNECT_PATH}?state={state}"}


@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
def receive_connection():
	"""Hub → this site: the credentials of a freshly connected WhatsApp number.

	Guest-accessible: the caller is the hub, not a logged-in user. It is
	authenticated by the relay signature over the exact body, so nobody else can
	inject an account.
	"""
	raw_body = frappe.request.get_data() or b""
	if not valid_relay_signature(frappe.request.headers.get("X-CRM-Relay-Signature"), raw_body):
		return Response("invalid signature", status=403, mimetype="text/plain")

	try:
		data = json.loads(raw_body)
	except ValueError:
		return Response("bad payload", status=400, mimetype="text/plain")

	if not whatsapp_installed():
		return Response("whatsapp app not installed", status=400, mimetype="text/plain")

	try:
		name = upsert_account(data)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "WhatsApp: could not store the connection")
		return Response("could not store account", status=500, mimetype="text/plain")

	frappe.db.commit()
	return Response(json.dumps({"ok": True, "account": name}), mimetype="application/json")


def upsert_account(data: dict) -> str:
	"""Create or refresh the frappe_whatsapp account for this number.

	Only fields the installed version actually has are written, so a different
	frappe_whatsapp release cannot break the connection.
	"""
	phone_id = data.get("phone_number_id")
	if not phone_id:
		frappe.throw(_("No phone number id in the connection payload"))

	values = {
		"token": data.get("token"),
		"phone_id": phone_id,
		"business_id": data.get("waba_id"),
		"app_id": get_app_id(),
		"webhook_verify_token": frappe.get_cached_value(
			"CRM Meta Settings", "CRM Meta Settings", "webhook_verify_token"
		),
		"status": "Active",
		"enabled": 1,
		"account_name": data.get("verified_name") or data.get("display_phone_number") or phone_id,
	}
	known = {df.fieldname for df in frappe.get_meta("WhatsApp Account").fields}
	# keep only what this frappe_whatsapp version understands
	values = {key: value for key, value in values.items() if key in known and value is not None}

	existing = frappe.db.get_value("WhatsApp Account", {"phone_id": phone_id}, "name")
	if existing:
		doc = frappe.get_doc("WhatsApp Account", existing)
		doc.update(values)
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc({"doctype": "WhatsApp Account", **values})
		doc.insert(ignore_permissions=True)

	# first number connected becomes the one messages go out from
	settings = frappe.get_doc("WhatsApp Settings")
	if not settings.get("default_outgoing_account"):
		settings.default_outgoing_account = doc.name
		settings.save(ignore_permissions=True)
	return doc.name


@frappe.whitelist(methods=["POST"])
def set_default_account(name: str) -> dict:
	_check_manager()
	settings = frappe.get_doc("WhatsApp Settings")
	settings.default_outgoing_account = name
	settings.save()
	return {"default_account": name}


@frappe.whitelist(methods=["POST"])
def disconnect(name: str) -> dict:
	"""Remove a number from this CRM. The WhatsApp Business app keeps working."""
	_check_manager()
	settings = frappe.get_doc("WhatsApp Settings")
	if settings.get("default_outgoing_account") == name:
		settings.default_outgoing_account = None
		settings.save(ignore_permissions=True)
	frappe.delete_doc("WhatsApp Account", name, ignore_permissions=True)
	return get_status()
