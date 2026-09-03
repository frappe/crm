# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Coexistence webhooks — the half frappe_whatsapp does not know about.

A number in Coexistence keeps being used from the phone, so Meta sends three
extra webhook fields that plain Cloud API integrations never see:

- `smb_message_echoes` — messages the business SENDS from the WhatsApp Business
  app. Without these the CRM would only ever show the customer's side.
- `history` — up to six months of past conversations, delivered in chunks after
  the business approves sharing during onboarding.
- `smb_app_state_sync` — the business's contacts.

frappe_whatsapp only understands the `messages` field, so these are turned into
`WhatsApp Message` documents here.

**Why the rows are written with `db_insert()`**: inserting an Outgoing
`WhatsApp Message` normally makes frappe_whatsapp send it through the API. These
messages have already been sent — from the phone — so running that would deliver
every message twice. `db_insert()` writes the row without the controller.
"""

import json

import frappe

from crm.integrations.api import get_contact_lead_or_deal_from_number

COEXISTENCE_FIELDS = ("smb_message_echoes", "history", "smb_app_state_sync")


def ingest_entry(entry: dict) -> dict:
	"""Handle one webhook entry; returns a small tally for the logs."""
	tally = {"echoes": 0, "history": 0, "contacts": 0}
	for change in entry.get("changes") or []:
		field = change.get("field")
		value = change.get("value") or {}
		if field == "smb_message_echoes":
			tally["echoes"] += ingest_echoes(value)
		elif field == "history":
			tally["history"] += ingest_history(value)
		elif field == "smb_app_state_sync":
			tally["contacts"] += ingest_state_sync(value)
	return tally


def business_number(value: dict) -> str:
	return ((value.get("metadata") or {}).get("display_phone_number") or "").lstrip("+")


def ingest_echoes(value: dict) -> int:
	"""Messages the business sent from the phone after onboarding."""
	stored = 0
	for message in value.get("message_echoes") or []:
		if store_message(message, business_number(value)):
			stored += 1
	return stored


def ingest_history(value: dict) -> int:
	"""Past conversations, delivered in chunks after the business opts in."""
	stored = 0
	ours = business_number(value)
	for chunk in value.get("history") or []:
		for thread in chunk.get("threads") or []:
			for message in thread.get("messages") or []:
				if store_message(message, ours, historical=True):
					stored += 1
	return stored


def ingest_state_sync(value: dict) -> int:
	"""The business's contacts. Only logged for now — creating CRM leads from a
	whole address book is a decision for the user, not a side effect of connecting."""
	contacts = [row for row in value.get("state_sync") or [] if row.get("type") == "contact"]
	if contacts:
		frappe.logger("whatsapp").info(f"Coexistence: {len(contacts)} contacts announced")
	return len(contacts)


def message_body(message: dict) -> tuple[str, str]:
	"""(text, content_type) for the message types worth storing as text."""
	kind = message.get("type") or "text"
	if kind == "text":
		return (message.get("text") or {}).get("body") or "", "text"
	if kind == "reaction":
		return (message.get("reaction") or {}).get("emoji") or "", "reaction"
	if kind in ("image", "video", "audio", "document", "sticker"):
		node = message.get(kind) or {}
		return node.get("caption") or f"[{kind}]", kind
	if kind == "location":
		node = message.get("location") or {}
		return node.get("name") or "[location]", "location"
	return f"[{kind}]", kind


def store_message(message: dict, our_number: str, historical: bool = False) -> bool:
	"""Idempotent by WhatsApp message id. Returns True when a row was written."""
	message_id = message.get("id")
	if not message_id or frappe.db.exists("WhatsApp Message", {"message_id": message_id}):
		return False

	sender = (message.get("from") or "").lstrip("+")
	recipient = (message.get("to") or "").lstrip("+")
	outgoing = bool(our_number) and sender == our_number
	counterparty = recipient if outgoing else sender
	text, content_type = message_body(message)

	values = {
		"doctype": "WhatsApp Message",
		"type": "Outgoing" if outgoing else "Incoming",
		"message_type": "Manual",
		"content_type": content_type,
		"message": text,
		"message_id": message_id,
		"to": counterparty if outgoing else our_number,
		"from": our_number if outgoing else sender,
		"status": "delivered" if historical else "sent",
	}
	if message.get("context", {}).get("id"):
		values["is_reply"] = 1
		values["reply_to_message_id"] = message["context"]["id"]

	try:
		reference, doctype = get_contact_lead_or_deal_from_number(counterparty)
		if doctype and reference:
			values["reference_doctype"] = doctype
			values["reference_name"] = reference
	except Exception:
		pass

	known = {df.fieldname for df in frappe.get_meta("WhatsApp Message").fields}
	doc = frappe.new_doc("WhatsApp Message")
	for key, value in values.items():
		if key == "doctype" or key in known:
			doc.set(key, value)
	doc.set_new_name()
	# db_insert: the message already went out from the phone, so the controller
	# must not run and send it again
	doc.db_insert()
	return True


def handle_account_update(value: dict) -> None:
	"""Onboarding milestones and account status changes."""
	frappe.logger("whatsapp").info(f"Coexistence account update: {json.dumps(value)[:500]}")
