# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json
from collections import Counter
from datetime import timedelta

import frappe
from frappe import _
from frappe.query_builder import Case, Field, Order
from frappe.query_builder.functions import Coalesce, Count, Min
from frappe.utils import now_datetime

from crm.fcrm.doctype.crm_dashboard.home_layout import role_for
from crm.fcrm.doctype.crm_dashboard.home_scope import Mine, Team
from crm.fcrm.doctype.crm_dashboard.home_widgets import (
	RECORD_TYPES,
	ROW_LIMIT,
	AssignedToMe,
	FollowUpsDue,
	NoNextStep,
	RecordWidget,
	RepliesWaiting,
)
from crm.fcrm.doctype.crm_dashboard.team_widgets import TeamOverdueFollowUps, TeamRepliesWaiting, Unassigned
from crm.fcrm.doctype.crm_task.rules import FOLLOW_UP_DOCTYPES

NEW_FOR_YOU_DAYS = 7
NO_SLA_WAIT_DAYS = 2
SHOW_ALL_LIMIT = 50
MINE_SLOTS = {"waiting": 2, "follow_ups": 2, "new": 1}
TEAM_SLOTS = {"clients": 3, "people": 2}


def past_response(table):
	"""WhatsApp and calls never record a first response, so an outbound message also counts as one."""
	return (
		(table.response_by < now_datetime())
		& table.first_responded_on.isnull()
		& table.last_outbound_at.isnull()
	)


def allocate(rows_by_group: dict, slots: dict) -> dict:
	"""Give each group its slots, then pass unused slots along in group order."""
	taken = {group: min(len(rows_by_group[group]), count) for group, count in slots.items()}
	spare = sum(slots.values()) - sum(taken.values())
	for group in slots:
		extra = min(spare, len(rows_by_group[group]) - taken[group])
		taken[group] += extra
		spare -= extra
	return {group: rows_by_group[group][:count] for group, count in taken.items()}


class NewForYou(AssignedToMe):
	def query(self, doctype: str, table):
		todo = frappe.qb.DocType("ToDo")
		return (
			super()
			.query(doctype, table)
			.where(todo.creation > now_datetime() - timedelta(days=NEW_FOR_YOU_DAYS))
			.where(Coalesce(todo.assigned_by, "") != self.scope.user)
			.where(table.last_outbound_at.isnull())
			.where(table.awaiting_reply_since.isnull())
		)

	def fields(self, doctype: str, table) -> list:
		return [*super().fields(doctype, table), table.source]


class WaitingOnMe(RepliesWaiting):
	def fields(self, doctype: str, table) -> list:
		past = Case().when(past_response(table), 1).else_(0).as_("past_response")
		return [*super().fields(doctype, table), past]


class NoNextStepNotListed(NoNextStep):
	"""Waiting records and new leads already have their own item in the Brief."""

	def filtered(self, doctype: str, table):
		query = super().filtered(doctype, table).where(table.awaiting_reply_since.isnull())
		if doctype != "CRM Lead":
			return query
		new_lead = frappe.qb.DocType("CRM Lead").as_("new_lead")
		new_leads = NewForYou(("CRM Lead",), self.scope).query("CRM Lead", new_lead).select(new_lead.name)
		return query.where(table.name.notin(new_leads))


class ClientsWaiting(TeamRepliesWaiting):
	sort_field = "waiting_since"

	def filtered(self, doctype: str, table):
		return self.active(doctype, table).where(
			table.awaiting_reply_since.isnotnull() | past_response(table)
		)

	def sort_term(self, table):
		return Coalesce(table.awaiting_reply_since, table.response_by).as_(self.sort_field)

	def rows(self) -> list:
		rows = []
		for doctype in self.doctypes:
			table = frappe.qb.DocType(doctype)
			past = Case().when(past_response(table), 1).else_(0).as_("past_response")
			query = self.query(doctype, table).select(
				*self.fields(doctype, table), self.sort_term(table), past
			)
			query = query.orderby(Field("past_response"), order=Order.desc).orderby(Field(self.sort_field))
			rows += [{**row, "doctype": doctype} for row in query.limit(ROW_LIMIT).run(as_dict=True)]
		rows.sort(key=lambda row: (-row["past_response"], row[self.sort_field]))
		return self.decorate(rows[:ROW_LIMIT])


class Ownerless(Unassigned):
	def filtered(self, doctype: str, table):
		owner = table[RECORD_TYPES[doctype].owner_field]
		return super().filtered(doctype, table).where(Coalesce(owner, "") == "")


class PastResponse(RecordWidget):
	def filtered(self, doctype: str, table):
		return super().filtered(doctype, table).where(past_response(table))


class WaitingTooLong(RepliesWaiting):
	def filtered(self, doctype: str, table):
		cutoff = now_datetime() - timedelta(days=NO_SLA_WAIT_DAYS)
		return super().filtered(doctype, table).where(table.awaiting_reply_since < cutoff)


def member_counts(widget: RecordWidget) -> Counter:
	"""Count each record for its owner, or for its first assignee when it has no owner."""
	counts = Counter()
	for doctype in widget.doctypes:
		table = frappe.qb.DocType(doctype)
		owner = table[RECORD_TYPES[doctype].owner_field]
		query = widget.query(doctype, table)
		has_owner = Coalesce(owner, "") != ""
		counts.update(dict(query.select(owner, Count("*")).where(has_owner).groupby(owner).run()))
		for (assigned,) in query.select(table._assign).where(Coalesce(owner, "") == "").run():
			first = next(iter(json.loads(assigned or "[]")), None)
			if first:
				counts[first] += 1
	return counts


class MineBrief:
	def __init__(self, user: str):
		self.scope = Mine(user)

	def widgets(self, row_limit: int = ROW_LIMIT) -> dict:
		widgets = {
			"waiting": WaitingOnMe(FOLLOW_UP_DOCTYPES, self.scope),
			"tasks": FollowUpsDue(FOLLOW_UP_DOCTYPES, self.scope),
			"idle": NoNextStepNotListed(FOLLOW_UP_DOCTYPES, self.scope),
			"new": NewForYou(("CRM Lead",), self.scope),
		}
		for widget in widgets.values():
			widget.row_limit = row_limit
		return widgets

	def summary(self, show_all: bool = False) -> dict:
		widgets = self.widgets(SHOW_ALL_LIMIT if show_all else ROW_LIMIT)
		counts = {key: widget.count() for key, widget in widgets.items()}
		rows = {
			"waiting": [{**row, "kind": "waiting"} for row in widgets["waiting"].rows()],
			"follow_ups": [
				*({**row, "kind": "follow_up"} for row in widgets["tasks"].rows()),
				*({**row, "kind": "no_next_step"} for row in widgets["idle"].rows()),
			],
			"new": new_items(widgets["new"].rows(), counts["new"]),
		}
		shown = rows if show_all else allocate(rows, MINE_SLOTS)
		set_last_emails(shown["waiting"])
		items = [item for group in shown.values() for item in group]
		available = counts["waiting"] + counts["tasks"] + counts["idle"] + bool(counts["new"])
		return {"items": items, "total": headline(counts), "available": available}

	def count(self) -> int:
		return headline({key: widget.count() for key, widget in self.widgets().items()})


def headline(counts: dict) -> int:
	"""Idle records count only when the Brief has room to show them, or they swamp the number."""
	taken = allocate(
		{
			"waiting": range(counts["waiting"]),
			"follow_ups": range(counts["tasks"] + counts["idle"]),
			"new": range(min(counts["new"], 1)),
		},
		MINE_SLOTS,
	)
	idle_shown = max(len(taken["follow_ups"]) - counts["tasks"], 0)
	return counts["waiting"] + counts["tasks"] + counts["new"] + idle_shown


def new_items(rows: list, count: int) -> list:
	if not rows:
		return []
	newest = rows[0]
	names = [row["title"] or row["name"] for row in rows[:3]]
	return [{**newest, "kind": "new", "count": count, "names": names}]


class TeamBrief:
	def __init__(self, user: str):
		self.scope = Team(user)

	def summary(self, show_all: bool = False) -> dict:
		clients = ClientsWaiting(FOLLOW_UP_DOCTYPES, self.scope)
		if show_all:
			clients.row_limit = SHOW_ALL_LIMIT
		rows = [{**row, "kind": "client"} for row in clients.rows()]
		ownerless = self.ownerless()
		if ownerless:
			past = [row for row in rows if row["past_response"]]
			rest = [row for row in rows if not row["past_response"]]
			rows = [*past, ownerless, *rest]
		people = [*self.workload(), *self.overdue_people()]
		total = clients.count() + bool(ownerless) + len(people)
		shown = {"clients": rows, "people": people}
		if not show_all:
			shown = allocate(shown, TEAM_SLOTS)
		set_last_emails(shown["clients"])
		items = [*shown["clients"], *shown["people"]]
		return {"items": items, "total": total, "available": total}

	def count(self) -> int:
		clients = ClientsWaiting(FOLLOW_UP_DOCTYPES, self.scope).count()
		return clients + bool(self.ownerless()) + len(self.workload()) + len(self.overdue_people())

	def ownerless(self) -> dict | None:
		widget = Ownerless(("CRM Lead",), self.scope)
		count = widget.count()
		if not count:
			return None
		table = frappe.qb.DocType("CRM Lead")
		oldest = widget.query("CRM Lead", table).select(Min(table.creation)).run()[0][0]
		return {"kind": "ownerless", "count": count, "since": oldest}

	def overdue_people(self) -> list:
		widget = TeamOverdueFollowUps(FOLLOW_UP_DOCTYPES, self.scope)
		task = widget.task
		rows = (
			widget.query()
			.select(task.assigned_to, Count("*"), Min(task.due_date))
			.groupby(task.assigned_to)
			.run()
		)
		return [
			{"kind": "overdue_person", "member": member, "count": count, "oldest_due": oldest}
			for member, count, oldest in sorted(rows, key=lambda row: (-row[1], row[0]))
		]

	def workload(self) -> list:
		has_sla = frappe.db.exists("CRM Service Level Agreement", {"enabled": 1})
		widget = PastResponse if has_sla else WaitingTooLong
		members = set(self.scope.members)
		behind = member_counts(widget(FOLLOW_UP_DOCTYPES, self.scope))
		behind = {member: count for member, count in behind.items() if member in members}
		if not behind:
			return []

		open_records = member_counts(RecordWidget(FOLLOW_UP_DOCTYPES, self.scope))
		spare = [
			member for member in members - set(behind) if member != self.scope.user and open_records[member]
		]
		lightest = min(spare, key=lambda member: (open_records[member], member), default=None)
		return [
			{
				"kind": "workload",
				"member": member,
				"behind": count,
				"past_response": bool(has_sla),
				"lightest": lightest,
				"lightest_open": open_records[lightest] if lightest else None,
			}
			for member, count in sorted(behind.items(), key=lambda item: (-item[1], item[0]))
		]


def set_last_emails(rows: list):
	for row in rows:
		if row.get("channel") != "email":
			continue
		references = [(row["doctype"], row["name"])]
		if row.get("lead"):
			references.append(("CRM Lead", row["lead"]))
		emails = [email for reference in references if (email := last_email(*reference))]
		if emails:
			row["last_email"] = max(emails, key=lambda email: email.date)


def last_email(doctype: str, name: str):
	emails = frappe.get_all(
		"Communication",
		filters={
			"reference_doctype": doctype,
			"reference_name": name,
			"communication_type": "Communication",
			"sent_or_received": "Received",
		},
		fields=[
			"sender_full_name as sender",
			"sender as sender_email",
			"subject",
			"communication_date as date",
		],
		order_by="communication_date desc",
		limit=1,
	)
	return emails[0] if emails and emails[0].date else None


def get_brief(user: str, tab: str = "mine", show_all: bool = False) -> dict:
	if role_for(user) != "manager":
		if tab != "mine":
			frappe.throw(_("The team brief is only available to managers"), frappe.PermissionError)
		return MineBrief(user).summary(show_all)

	if tab not in ("team", "mine"):
		frappe.throw(_("Unknown brief tab {0}").format(tab))
	active, other = (TeamBrief, MineBrief) if tab == "team" else (MineBrief, TeamBrief)
	brief = active(user).summary(show_all)
	brief["counts"] = {tab: brief["total"], "mine" if tab == "team" else "team": other(user).count()}
	return brief
