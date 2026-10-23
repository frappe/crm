# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Manager-only Home widgets, run on a Team scope."""

import json
from datetime import timedelta

import frappe
from frappe.query_builder import Field
from frappe.query_builder.functions import Coalesce, Count, Sum
from frappe.utils import now_datetime

from crm.fcrm.doctype.crm_dashboard.home_widgets import (
	RECORD_TYPES,
	NewLeads,
	NoNextStep,
	RecordWidget,
	RepliesWaiting,
	TaskWidget,
	Widget,
)
from crm.fcrm.doctype.crm_task.rules import FOLLOW_UP_DOCTYPES

# older overdue tasks are mostly abandoned and would bury the recent misses
OVERDUE_DAYS = 30
# unassigned new leads can run into the hundreds of thousands, so they are counted up to here
UNASSIGNED_CAP = 100
OVERVIEW_CACHE_SECONDS = 180
RESPONSE_DAYS = 30
OVERVIEW_COUNTS = {"open": RecordWidget, "replies_waiting": RepliesWaiting, "no_next_step": NoNextStep}


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


class TeamOverview(Widget):
	"""Per team member: the counts their own widgets show, and their average first response
	time on records created in the last RESPONSE_DAYS. Cached per scope, as it groups over
	every record of the team."""

	def summary(self) -> dict:
		key = f"crm:home:team_overview:{self.scope.key}"
		rows = frappe.cache.get_value(key)
		if rows is None:
			rows = self.rows()
			frappe.cache.set_value(key, rows, expires_in_sec=OVERVIEW_CACHE_SECONDS)
		return {"rows": rows}

	def rows(self) -> list:
		stats = {
			member: dict.fromkeys((*OVERVIEW_COUNTS, "overdue_follow_ups"), 0)
			for member in self.scope.members
		}
		for doctype in FOLLOW_UP_DOCTYPES:
			table = frappe.qb.DocType(doctype)
			for stat, widget in OVERVIEW_COUNTS.items():
				records = self.by_member(doctype, widget(self.doctypes, self.scope).filtered(doctype, table))
				for member, count in (
					frappe.qb.from_(records).select("member", Count("*")).groupby("member").run()
				):
					stats[member][stat] += count

		for member, count in self.overdue_follow_ups():
			stats[member]["overdue_follow_ups"] = count

		response_times = self.first_response_times()
		return [
			{"user": member, **counts, "first_response_time": response_times.get(member)}
			for member, counts in stats.items()
		]

	def overdue_follow_ups(self) -> list:
		follow_ups = TeamOverdueFollowUps(FOLLOW_UP_DOCTYPES, self.scope)
		assignee = follow_ups.task.assigned_to
		return follow_ups.query().select(assignee, Count("*")).groupby(assignee).run()

	def first_response_times(self) -> dict:
		totals = {}
		since = now_datetime() - timedelta(days=RESPONSE_DAYS)
		for doctype in FOLLOW_UP_DOCTYPES:
			table = frappe.qb.DocType(doctype)
			responded = frappe.qb.from_(table).where(
				(table.creation >= since) & table.first_response_time.isnotnull()
			)
			records = self.by_member(doctype, responded, table.first_response_time)
			response_time = Field("first_response_time")
			query = frappe.qb.from_(records).select("member", Sum(response_time), Count(response_time))
			for member, seconds, count in query.groupby("member").run():
				total_seconds, total_count = totals.get(member, (0, 0))
				totals[member] = (total_seconds + seconds, total_count + count)
		return {member: round(seconds / count) for member, (seconds, count) in totals.items()}

	def by_member(self, doctype: str, query, *fields):
		"""Each record of `query` once per member who owns it or has it assigned, like Mine."""
		table = frappe.qb.DocType(doctype)
		todo = frappe.qb.DocType("ToDo")
		owner = table[RECORD_TYPES[doctype].owner_field]
		members = self.scope.members or [None]
		owned = query.select(owner.as_("member"), table.name, *fields).where(owner.isin(members))
		assigned = (
			query.join(todo)
			.on((todo.reference_type == doctype) & (todo.reference_name == table.name))
			.select(todo.allocated_to.as_("member"), table.name, *fields)
			.where((todo.status == "Open") & todo.allocated_to.isin(members))
		)
		return owned.union(assigned)


TEAM_WIDGET_DATA = {
	"team_overview": TeamOverview,
	"team_replies_waiting": TeamRepliesWaiting,
	"team_overdue_follow_ups": TeamOverdueFollowUps,
	"unassigned": Unassigned,
}


def set_owners(rows: list):
	"""Fall back to the first assignee for records without an owner."""
	for row in rows:
		assigned = json.loads(row.pop("_assign") or "[]")
		row["owner"] = row["owner"] or next(iter(assigned), None)
