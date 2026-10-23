# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Manager-only Home widgets, run on a Team scope."""

import json

import frappe
from frappe.query_builder.functions import Coalesce, Count

from crm.fcrm.doctype.crm_dashboard.home_widgets import (
	RECORD_TYPES,
	NewLeads,
	RepliesWaiting,
	TaskWidget,
)

# older overdue tasks are mostly abandoned and would bury the recent misses
OVERDUE_DAYS = 30
# unassigned new leads can run into the hundreds of thousands, so they are counted up to here
UNASSIGNED_CAP = 100


class TeamRepliesWaiting(RepliesWaiting):
	def fields(self, doctype: str, table) -> list:
		owner = table[RECORD_TYPES[doctype].owner_field].as_("owner")
		return [*super().fields(doctype, table), owner, table._assign]

	def decorate(self, rows: list) -> list:
		set_owners(rows)
		return super().decorate(rows)


class TeamOverdueFollowUps(TaskWidget):
	FIELDS = (*TaskWidget.FIELDS, "assigned_to")

	def condition(self):
		return self.linked() & self.due.overdue_within_condition(self.task, OVERDUE_DAYS)


class Unassigned(NewLeads):
	sort_field = "creation"
	descending = True

	def filtered(self, doctype: str, table):
		return super().filtered(doctype, table).where(Coalesce(table._assign, "").isin(("", "[]")))

	def summary(self) -> dict:
		total = self.count()
		return {"rows": self.rows(), "total": min(total, UNASSIGNED_CAP), "more": total > UNASSIGNED_CAP}

	def _count(self, doctype: str) -> int:
		table = frappe.qb.DocType(doctype)
		query = self.query(doctype, table).select(table.name).limit(UNASSIGNED_CAP + 1)
		return frappe.qb.from_(query).select(Count("*")).run()[0][0]


TEAM_WIDGET_DATA = {
	"team_replies_waiting": TeamRepliesWaiting,
	"team_overdue_follow_ups": TeamOverdueFollowUps,
	"unassigned": Unassigned,
}


def set_owners(rows: list):
	"""Fall back to the first assignee for records without an owner."""
	for row in rows:
		assigned = json.loads(row.pop("_assign") or "[]")
		row["owner"] = row["owner"] or next(iter(assigned), None)
