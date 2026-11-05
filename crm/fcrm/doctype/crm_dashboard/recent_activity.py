# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The leads and deals a user worked on or opened lately, one row per record with its latest action,
built from the records each action leaves behind, as Helpdesk's recent activity does for tickets."""

import json
from dataclasses import dataclass

import frappe
from frappe import _
from frappe.utils import add_days, now_datetime

from crm.fcrm.doctype.crm_dashboard.home_widgets import RECORD_TYPES, ROW_LIMIT, Widget

ACTIVITY_DAYS = 7
# Each source is read newest first and capped: only the latest rows can make the card.
PER_SOURCE_LIMIT = ROW_LIMIT * 20


@dataclass(frozen=True)
class Source:
	doctype: str
	user_field: str
	doctype_field: str
	name_field: str
	activity: str
	filters: tuple = ()


SOURCES = (
	Source("View Log", "viewed_by", "reference_doctype", "reference_name", "viewed"),
	Source(
		"Communication",
		"owner",
		"reference_doctype",
		"reference_name",
		"emailed",
		(("communication_type", "Communication"), ("sent_or_received", "Sent")),
	),
	Source(
		"Comment",
		"owner",
		"reference_doctype",
		"reference_name",
		"commented",
		(("comment_type", "Comment"),),
	),
	Source("FCRM Note", "owner", "reference_doctype", "reference_docname", "noted"),
	Source("CRM Task", "owner", "reference_doctype", "reference_docname", "added_task"),
	Source("CRM Call Log", "owner", "reference_doctype", "reference_docname", "called"),
	Source(
		"WA Message",
		"owner",
		"reference_doctype",
		"reference_docname",
		"messaged",
		(("direction", "Outgoing"),),
	),
	Source("ToDo", "assigned_by", "reference_type", "reference_name", "assigned"),
	Source("Version", "owner", "ref_doctype", "docname", "updated"),
)


class RecentActivity(Widget):
	def summary(self) -> dict:
		latest = {}
		for event in sorted(self.events(), key=lambda event: event["at"]):
			latest[event["doctype"], event["name"]] = event

		records = self.readable_records(latest)
		rows = [
			{**records[key], **event, "activity": activity_label(event)}
			for key, event in latest.items()
			if key in records
		]
		rows.sort(key=lambda row: row["at"], reverse=True)
		return {
			"rows": [{key: value for key, value in row.items() if key != "data"} for row in rows[:ROW_LIMIT]]
		}

	def events(self) -> list:
		since = add_days(now_datetime(), -ACTIVITY_DAYS)
		events = []
		for source in SOURCES:
			if not frappe.db.table_exists(source.doctype):
				continue
			fields = [
				f"{source.doctype_field} as doctype",
				f"{source.name_field} as name",
				"creation as at",
			]
			if source.activity == "updated":
				fields.append("data")
			rows = frappe.get_all(
				source.doctype,
				filters={
					**dict(source.filters),
					source.user_field: self.scope.user,
					source.doctype_field: ["in", self.doctypes],
					"creation": [">=", since],
				},
				fields=fields,
				order_by="creation desc",
				limit=PER_SOURCE_LIMIT,
			)
			events += [{**row, "activity_type": source.activity} for row in rows if row.name]
		return events

	def readable_records(self, latest: dict) -> dict:
		"""get_list applies permissions, so records the user can no longer read drop out."""
		records = {}
		for doctype in self.doctypes:
			names = [name for record_doctype, name in latest if record_doctype == doctype]
			if not names:
				continue
			record_type = RECORD_TYPES[doctype]
			for record in frappe.get_list(
				doctype,
				filters={"name": ["in", names]},
				fields=[
					"name",
					"status",
					f"{record_type.title_field} as title",
					f"{record_type.subtitle_field} as subtitle",
				],
			):
				records[doctype, record.name] = {**record, "doctype": doctype}
		return records


def activity_label(event: dict) -> str:
	if event["activity_type"] == "updated":
		return updated_label(event.get("data")) or _("Updated")
	return {
		"viewed": _("Viewed"),
		"emailed": _("Sent an email"),
		"commented": _("Commented"),
		"noted": _("Added a note"),
		"added_task": _("Added a task"),
		"called": _("Logged a call"),
		"messaged": _("Sent a WhatsApp message"),
		"assigned": _("Assigned"),
	}[event["activity_type"]]


def updated_label(data: str | None) -> str | None:
	"""The most telling change in a Version, as Helpdesk names it."""
	try:
		changed = {field: new for field, _old, new in json.loads(data or "{}").get("changed") or []}
	except (ValueError, TypeError):
		return None
	if changed.get("status"):
		return _("Set status to {0}").format(_(changed["status"]))
	if changed.keys() & {"lead_owner", "deal_owner"}:
		return _("Changed owner")
	return None
