# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""In-app alerts to a lead's or deal's assignees when a customer message comes in."""

from dataclasses import dataclass

import frappe
from frappe import _

from crm.api.doc import get_assigned_users
from crm.fcrm.doctype.crm_dashboard.home_widgets import RECORD_TYPES
from crm.fcrm.doctype.crm_notification.crm_notification import (
	get_record_title,
	highlight,
	notification_html,
	notify_user,
	record_label,
)
from crm.utils import is_unattended


@dataclass(frozen=True)
class Reply:
	"""An inbound message, as the channel that received it describes it."""

	channel: str
	source_doctype: str
	source_name: str
	sender_name: str
	preview: str | None = None
	sender_user: str | None = None


def alert_assignees(doctype: str, docname: str, reply: Reply):
	if is_unattended():
		return

	text = notification_html(
		channel_text(reply.channel).format(
			highlight(reply.sender_name),
			record_label(doctype),
			highlight(get_record_title(doctype, docname)),
		)
	)
	for user in recipients(doctype, docname):
		notify_user(
			{
				"owner": reply.sender_user,
				"assigned_to": user,
				"notification_type": "Reply",
				"message": reply.preview,
				"notification_text": text,
				"reference_doctype": reply.source_doctype,
				"reference_docname": reply.source_name,
				"redirect_to_doctype": doctype,
				"redirect_to_docname": docname,
			}
		)


def recipients(doctype: str, docname: str) -> list:
	owner = frappe.db.get_value(doctype, docname, RECORD_TYPES[doctype].owner_field)
	return get_assigned_users(doctype, docname, default_assigned_to=owner)


def channel_text(channel: str) -> str:
	return {
		"Email": _("{0} sent an email on {1} {2}"),
		"WhatsApp": _("{0} sent a WhatsApp message on {1} {2}"),
	}[channel]
