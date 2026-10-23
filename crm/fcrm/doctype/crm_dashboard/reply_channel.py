# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Which channel a waiting reply came in on, looked up for the few rows a widget shows.

The channel is not stored with `last_inbound_at`, so the latest inbound email and WhatsApp
message of each record are compared instead. A deal also gets the messages of the lead
it was converted from, as interactions on a converted lead are forwarded to its deal.
"""

import frappe
from frappe.query_builder.functions import Coalesce, Max


def set_reply_channels(rows: list):
	references = {}
	for row in rows:
		for doctype, name in _references(row):
			references.setdefault(doctype, set()).add(name)

	latest = {"email": _latest_emails(references), "whatsapp": _latest_whatsapp(references)}
	for row in rows:
		row["channel"] = _channel(row, latest)


def _channel(row: dict, latest: dict) -> str | None:
	received = {
		channel: max((at[ref] for ref in _references(row) if ref in at), default=None)
		for channel, at in latest.items()
	}
	received = {channel: at for channel, at in received.items() if at}
	return max(received, key=received.get) if received else None


def _references(row: dict) -> list:
	references = [(row["doctype"], row["name"])]
	if row.get("lead"):
		references.append(("CRM Lead", row["lead"]))
	return references


def _latest_emails(references: dict) -> dict:
	communication = frappe.qb.DocType("Communication")
	inbound = (communication.communication_type == "Communication") & (
		communication.sent_or_received == "Received"
	)
	return _latest(
		communication,
		communication.reference_name,
		Coalesce(communication.communication_date, communication.creation),
		inbound,
		references,
	)


def _latest_whatsapp(references: dict) -> dict:
	if not frappe.db.table_exists("WA Message"):
		return {}
	message = frappe.qb.DocType("WA Message")
	# a reaction is not a message, as in crm.api.whatsapp.record_interaction
	inbound = (
		(message.direction == "Incoming") & (message.docstatus == 1) & (Coalesce(message.reaction, "") == "")
	)
	return _latest(
		message, message.reference_docname, Coalesce(message.timestamp, message.creation), inbound, references
	)


def _latest(table, name_field, received_at, inbound, references: dict) -> dict:
	latest = {}
	for doctype, names in references.items():
		rows = (
			frappe.qb.from_(table)
			.select(name_field, Max(received_at))
			.where(inbound & (table.reference_doctype == doctype) & name_field.isin(list(names)))
			.groupby(name_field)
			.run()
		)
		for name, at in rows:
			latest[doctype, name] = at
	return latest
