# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json
import operator
from datetime import timedelta
from functools import reduce

import frappe
from frappe.query_builder import Case, Field
from frappe.query_builder.functions import Coalesce, Count, Sum
from frappe.utils import now_datetime

from crm.fcrm.doctype.crm_dashboard.home_layout import DEFAULT_PERIOD, period_days
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

OVERDUE_DAYS = 30
UNASSIGNED_CAP = 100
OVERVIEW_CACHE_SECONDS = 180
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
	"""Every column counts only leads and deals created in the period."""

	def __init__(self, doctypes: tuple, scope, period: str = DEFAULT_PERIOD):
		super().__init__(doctypes, scope)
		self.since = now_datetime() - timedelta(days=period_days(period))
		self.period = period

	def summary(self) -> dict:
		key = f"crm:home:team_overview:{self.scope.key}:{self.period}"
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
				filtered = widget(self.doctypes, self.scope).filtered(doctype, table)
				records = self.by_member(doctype, filtered.where(table.creation >= self.since))
				counts = frappe.qb.from_(records).select("member", Count("*")).groupby("member")
				for member, count in counts.run():
					stats[member][stat] += count

		for member, count in self.overdue_follow_ups():
			stats[member]["overdue_follow_ups"] = count

		responses = self.responses()
		no_responses = {"first_response_time": None, "sla_met": 0, "sla_total": 0}
		return [
			{"user": member, **counts, **responses.get(member, no_responses)}
			for member, counts in stats.items()
		]

	def overdue_follow_ups(self) -> list:
		follow_ups = TeamOverdueFollowUps(FOLLOW_UP_DOCTYPES, self.scope)
		task = follow_ups.task
		on_recent_records = reduce(
			operator.or_,
			(
				(task.reference_doctype == doctype) & task.reference_docname.isin(self.created(doctype))
				for doctype in FOLLOW_UP_DOCTYPES
			),
		)
		query = follow_ups.query().where(on_recent_records)
		return query.select(task.assigned_to, Count("*")).groupby(task.assigned_to).run()

	def created(self, doctype: str):
		table = frappe.qb.DocType(doctype)
		return frappe.qb.from_(table).select(table.name).where(table.creation >= self.since)

	def responses(self) -> dict:
		"""An unanswered record counts against the SLA once its response_by has passed."""
		now = now_datetime()
		totals = {}
		for doctype in FOLLOW_UP_DOCTYPES:
			table = frappe.qb.DocType(doctype)
			created = frappe.qb.from_(table).where(table.creation >= self.since)
			sla_decided = table.response_by.isnotnull() & (
				table.first_responded_on.isnotnull() | (table.response_by < now)
			)
			records = self.by_member(
				doctype,
				created,
				table.first_response_time,
				Case().when(table.first_responded_on <= table.response_by, 1).else_(0).as_("sla_met"),
				Case().when(sla_decided, 1).else_(0).as_("sla_total"),
			)
			response_time = Field("first_response_time")
			query = frappe.qb.from_(records).select(
				"member",
				Sum(response_time),
				Count(response_time),
				Sum(Field("sla_met")),
				Sum(Field("sla_total")),
			)
			for member, *values in query.groupby("member").run():
				previous = totals.get(member, (0, 0, 0, 0))
				totals[member] = tuple(
					total + (value or 0) for total, value in zip(previous, values, strict=True)
				)
		return {
			member: {
				"first_response_time": round(seconds / count) if count else None,
				"sla_met": int(met),
				"sla_total": int(total),
			}
			for member, (seconds, count, met, total) in totals.items()
		}

	def by_member(self, doctype: str, query, *fields):
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
	for row in rows:
		assigned = json.loads(row.pop("_assign") or "[]")
		row["owner"] = row["owner"] or next(iter(assigned), None)
