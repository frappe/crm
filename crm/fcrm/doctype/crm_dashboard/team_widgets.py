# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import hashlib
import json
import operator
from datetime import timedelta
from functools import reduce
from typing import ClassVar

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
	TabbedWidget,
	TaskWidget,
	Widget,
	check_filters,
)

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

	def count(self) -> int:
		return min(super().count(), UNASSIGNED_CAP)

	def _count(self, doctype: str) -> int:
		table = frappe.qb.DocType(doctype)
		query = self.query(doctype, table).select(table.name).limit(UNASSIGNED_CAP + 1)
		return frappe.qb.from_(query).select(Count("*")).run()[0][0]


class TeamOverview(Widget):
	"""Every column counts only leads and deals created in the period that match the filters.
	With both doctypes, the filters can only use fields the two share."""

	def __init__(self, doctypes: tuple, scope, period: str = DEFAULT_PERIOD, filters: dict | None = None):
		super().__init__(doctypes, scope)
		self.since = now_datetime() - timedelta(days=period_days(period))
		self.period = period
		self.filters = filters or {}
		check_filters(doctypes, self.filters)

	def summary(self) -> dict:
		key = overview_cache_key(self.scope.key, self.period, self.doctypes, self.filters)
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
		for doctype in self.doctypes:
			table = frappe.qb.DocType(doctype)
			for stat, widget in OVERVIEW_COUNTS.items():
				filtered = widget(self.doctypes, self.scope).filtered(doctype, table)
				records = self.by_member(doctype, filtered.where(self.counted(doctype, table)))
				counts = frappe.qb.from_(records).select("member", Count("*")).groupby("member")
				for member, count in counts.run():
					stats[member][stat] += count

		for member, count in self.overdue_follow_ups():
			stats[member]["overdue_follow_ups"] = count

		responses = self.responses()
		no_responses = {"first_response_time": None, "sla_met": 0, "sla_total": 0}
		rows = [
			{"user": member, **counts, **responses.get(member, no_responses)}
			for member, counts in stats.items()
		]
		return [row for row in rows if has_figures(row)]

	def overdue_follow_ups(self) -> list:
		follow_ups = TeamOverdueFollowUps(self.doctypes, self.scope)
		task = follow_ups.task
		on_recent_records = reduce(
			operator.or_,
			(
				(task.reference_doctype == doctype) & task.reference_docname.isin(self.created(doctype))
				for doctype in self.doctypes
			),
		)
		query = follow_ups.query().where(on_recent_records)
		return query.select(task.assigned_to, Count("*")).groupby(task.assigned_to).run()

	def created(self, doctype: str):
		table = frappe.qb.DocType(doctype)
		return frappe.qb.from_(table).select(table.name).where(self.counted(doctype, table))

	def counted(self, doctype: str, table):
		created = table.creation >= self.since
		if not self.filters:
			return created
		matching = frappe.qb.get_query(doctype, fields=["name"], filters=self.filters, db_query_compat=True)
		return created & table.name.isin(matching)

	def responses(self) -> dict:
		"""An unanswered record counts against the SLA once its response_by has passed."""
		now = now_datetime()
		totals = {}
		for doctype in self.doctypes:
			table = frappe.qb.DocType(doctype)
			created = frappe.qb.from_(table).where(self.counted(doctype, table))
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


class OverdueAndUnassigned(TabbedWidget):
	TABS: ClassVar[dict] = {"overdue": TeamOverdueFollowUps, "unassigned": Unassigned}


def overview_cache_key(scope_key: str, period: str, doctypes: tuple, filters: dict | None = None) -> str:
	key = f"crm:home:team_overview:{scope_key}:{period}:{','.join(doctypes)}"
	if filters:
		key += ":" + hashlib.sha1(json.dumps(filters, sort_keys=True).encode()).hexdigest()[:12]
	return key


def has_figures(row: dict) -> bool:
	counts = (*OVERVIEW_COUNTS, "overdue_follow_ups", "sla_total")
	return any(row[count] for count in counts) or row["first_response_time"] is not None


TEAM_WIDGET_DATA = {
	"team_overview": TeamOverview,
	"team_replies_waiting": TeamRepliesWaiting,
}

TEAM_TABBED_WIDGETS = {"overdue_and_unassigned": OverdueAndUnassigned}


def set_owners(rows: list):
	for row in rows:
		assigned = json.loads(row.pop("_assign") or "[]")
		row["owner"] = row["owner"] or next(iter(assigned), None)
