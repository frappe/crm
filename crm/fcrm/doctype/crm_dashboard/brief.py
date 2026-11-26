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
	DOCTYPES,
	RECORD_TYPES,
	ROW_LIMIT,
	AssignedToMe,
	FollowUpsDue,
	NoNextStep,
	RecordWidget,
	RepliesWaiting,
	TaskWidget,
	idle_since,
)
from crm.fcrm.doctype.crm_dashboard.team_widgets import (
	OVERDUE_DAYS,
	TeamOverdueFollowUps,
	TeamRepliesWaiting,
	Unassigned,
)

DOCTYPE_KEY = "crm_brief_doctype"
TAB_KEY = "crm_brief_tab"
RECORD_DOCTYPES = {"Lead": "CRM Lead", "Deal": "CRM Deal"}
RECORD_KEYS = {doctype: key for key, doctype in RECORD_DOCTYPES.items()}
NEW_FOR_YOU_DAYS = 7
NO_SLA_WAIT_DAYS = 2
# The Brief links to the records it had no room for; the link carries their names.
MORE_LIMIT = 100
# Idle records stay out, as they stay out of the headline.
MORE_KINDS = ("waiting", "follow_up", "client")
MINE_SLOTS = {"waiting": 2, "follow_ups": 2, "new": 1}
TEAM_SLOTS = {"clients": 3, "people": 2}


def past_response(table):
	"""WhatsApp and calls never record a first response, so an outbound message also counts as one."""
	return (
		(table.response_by < now_datetime())
		& table.first_responded_on.isnull()
		& table.last_outbound_at.isnull()
	)


def window_start():
	return now_datetime() - timedelta(days=OVERDUE_DAYS)


def waiting_in_window(table):
	return table.awaiting_reply_since >= window_start()


def past_response_in_window(table):
	return past_response(table) & (table.response_by >= window_start())


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
	def filtered(self, doctype: str, table):
		return super().filtered(doctype, table).where(waiting_in_window(table))

	def fields(self, doctype: str, table) -> list:
		past = Case().when(past_response(table), 1).else_(0).as_("past_response")
		return [*super().fields(doctype, table), past]


class NoNextStepNotListed(NoNextStep):
	"""Waiting records and new leads already have their own item in the Brief."""

	def filtered(self, doctype: str, table):
		query = (
			super()
			.filtered(doctype, table)
			.where(idle_since(table) >= window_start())
			.where(table.awaiting_reply_since.isnull())
		)
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
			rows += [{**row, "doctype": doctype} for row in query.limit(self.row_limit).run(as_dict=True)]
		rows.sort(key=lambda row: (-row["past_response"], row[self.sort_field]))
		return self.decorate(rows[: self.row_limit])


class RecentClientsWaiting(ClientsWaiting):
	def filtered(self, doctype: str, table):
		recent = waiting_in_window(table) | past_response_in_window(table)
		return super().filtered(doctype, table).where(recent)


class RecentFollowUpsDue(FollowUpsDue):
	def condition(self):
		return self.linked() & self.due.due_by_today_within_condition(self.task, OVERDUE_DAYS)


class OverdueFollowUps(TaskWidget):
	def condition(self):
		return self.linked() & self.due.overdue_condition(self.task)


class OlderRecords(RecordWidget):
	"""The records a widget counts that its 30-day version leaves out."""

	def __init__(self, widget: RecordWidget, recent: RecordWidget):
		super().__init__(widget.doctypes, widget.scope)
		self.widget = widget
		self.recent = recent

	def query(self, doctype: str, table):
		recent = self.recent.query(doctype, table).select(table.name)
		return self.widget.query(doctype, table).where(table.name.notin(recent))

	def counts(self) -> dict:
		return {doctype: self._count(doctype) for doctype in self.doctypes}

	def names(self, doctype: str) -> list:
		table = frappe.qb.DocType(doctype)
		return self.query(doctype, table).select(table.name).run(pluck=True)


class OlderTasks(TaskWidget):
	"""The tasks a widget counts that its 30-day version leaves out."""

	def __init__(self, widget: TaskWidget, recent: TaskWidget):
		super().__init__(widget.doctypes, widget.scope)
		self.widget = widget
		self.recent = recent

	def query(self):
		recent = self.recent.query().select(self.task.name)
		return self.widget.query().where(self.task.name.notin(recent))

	def names(self) -> list:
		return self.query().select(self.task.name).run(pluck=True)


class Ownerless(Unassigned):
	def filtered(self, doctype: str, table):
		owner = table[RECORD_TYPES[doctype].owner_field]
		return super().filtered(doctype, table).where(Coalesce(owner, "") == "")


class PastResponse(RecordWidget):
	def filtered(self, doctype: str, table):
		return super().filtered(doctype, table).where(past_response_in_window(table))


class WaitingTooLong(RepliesWaiting):
	def filtered(self, doctype: str, table):
		cutoff = now_datetime() - timedelta(days=NO_SLA_WAIT_DAYS)
		return (
			super()
			.filtered(doctype, table)
			.where(waiting_in_window(table) & (table.awaiting_reply_since < cutoff))
		)


class RecentlyWorked(RecordWidget):
	"""Any status counts, so a seller who just closed a deal is still active."""

	def filtered(self, doctype: str, table):
		# Same as idle_since(table) >= since, but plain comparisons run faster than GREATEST on large tables.
		since = window_start()
		worked = (
			(table.modified >= since) | (table.last_inbound_at >= since) | (table.last_outbound_at >= since)
		)
		return frappe.qb.from_(table).where(worked)


def member_counts(widget: RecordWidget) -> Counter:
	return sum(member_counts_by_doctype(widget).values(), Counter())


def member_counts_by_doctype(widget: RecordWidget) -> dict[str, Counter]:
	"""Count each record for its owner, or for its first assignee when it has no owner."""
	return {doctype: doctype_member_counts(widget, doctype) for doctype in widget.doctypes}


def doctype_member_counts(widget: RecordWidget, doctype: str) -> Counter:
	table = frappe.qb.DocType(doctype)
	owner = table[RECORD_TYPES[doctype].owner_field]
	query = widget.query(doctype, table)
	has_owner = Coalesce(owner, "") != ""
	counts = Counter(dict(query.select(owner, Count("*")).where(has_owner).groupby(owner).run()))
	for (assigned,) in query.select(table._assign).where(ownerless_assigned(table, owner)).run():
		if first := first_assignee(assigned):
			counts[first] += 1
	return counts


def member_names(widget: RecordWidget, doctype: str, member: str) -> list:
	"""The records that member_counts credits to one member."""
	table = frappe.qb.DocType(doctype)
	owner = table[RECORD_TYPES[doctype].owner_field]
	query = widget.query(doctype, table)
	owned = query.select(table.name).where(owner == member).run(pluck=True)
	assigned = query.select(table.name, table._assign).where(ownerless_assigned(table, owner)).run()
	return owned + [name for name, assign in assigned if first_assignee(assign) == member]


def ownerless_assigned(table, owner):
	return (Coalesce(owner, "") == "") & Coalesce(table._assign, "").notin(("", "[]"))


def first_assignee(assigned: str | None) -> str | None:
	return next(iter(json.loads(assigned or "[]")), None)


def has_sla() -> bool:
	return bool(frappe.db.exists("CRM Service Level Agreement", {"enabled": 1}))


class Brief:
	def older(self) -> dict:
		"""Conversations are counted per record type, as each type opens its own list."""
		widgets = self.older_widgets()
		counts = widgets["conversations"].counts()
		conversations = {
			key: counts[doctype] for key, doctype in RECORD_DOCTYPES.items() if doctype in counts
		}
		return without_zeros(
			{"conversations": without_zeros(conversations), "tasks": widgets["tasks"].count()}
		)

	def record_names(self, kind: str, doctype: str | None = None, member: str | None = None) -> list:
		if kind == "tasks":
			return self.older_widgets()["tasks"].names()
		if kind == "conversations":
			return self.older_widgets()["conversations"].names(self.record_doctype(doctype))
		frappe.throw(_("Unknown brief list {0}").format(kind))

	def record_doctype(self, doctype: str | None) -> str:
		record_doctype = RECORD_DOCTYPES.get(doctype)
		if record_doctype not in self.doctypes:
			frappe.throw(_("The brief does not show {0}").format(doctype))
		return record_doctype


class MineBrief(Brief):
	def __init__(self, user: str):
		self.scope = Mine(user)
		self.doctype = brief_doctype(user)
		self.doctypes = DOCTYPES[self.doctype]

	def widgets(self) -> dict:
		widgets = {
			"waiting": WaitingOnMe(self.doctypes, self.scope),
			"tasks": RecentFollowUpsDue(self.doctypes, self.scope),
			"idle": NoNextStepNotListed(self.doctypes, self.scope),
		}
		if "CRM Lead" in self.doctypes:
			widgets["new"] = NewForYou(("CRM Lead",), self.scope)
		return widgets

	def summary(self) -> dict:
		widgets = self.widgets()
		widgets["waiting"].row_limit = widgets["tasks"].row_limit = MORE_LIMIT
		counts = {key: widget.count() for key, widget in widgets.items()}
		rows = {
			"waiting": [{**row, "kind": "waiting"} for row in widgets["waiting"].rows()],
			"follow_ups": [
				*({**row, "kind": "follow_up"} for row in widgets["tasks"].rows()),
				*({**row, "kind": "no_next_step"} for row in widgets["idle"].rows()),
			],
			"new": new_items(widgets["new"].rows(), counts["new"]) if "new" in widgets else [],
		}
		shown = allocate(rows, MINE_SLOTS)
		set_last_emails(shown["waiting"])
		items = [item for group in shown.values() for item in group]
		return {
			"items": items,
			"total": headline(counts),
			"more": more_records(rows, shown),
			"older": self.older(),
		}

	def count(self) -> int:
		return headline({key: widget.count() for key, widget in self.widgets().items()})

	def older_widgets(self) -> dict:
		return {
			"conversations": OlderRecords(
				RepliesWaiting(self.doctypes, self.scope), WaitingOnMe(self.doctypes, self.scope)
			),
			"tasks": OlderTasks(
				FollowUpsDue(self.doctypes, self.scope), RecentFollowUpsDue(self.doctypes, self.scope)
			),
		}


def headline(counts: dict) -> int:
	"""Idle records count only when the Brief has room to show them, or they swamp the number."""
	counts = {"new": 0, **counts}
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


def more_records(rows: dict, shown: dict) -> dict:
	"""Names of the records each group had no room for, by the list that opens them."""
	more = {}
	for group, group_rows in rows.items():
		for row in group_rows[len(shown[group]) :]:
			if row["kind"] in MORE_KINDS:
				doctype = "CRM Task" if row["kind"] == "follow_up" else row["doctype"]
				more.setdefault(doctype, []).append(row["name"])
	return more


def new_items(rows: list, count: int) -> list:
	if not rows:
		return []
	newest = rows[0]
	names = [row["title"] or row["name"] for row in rows[:3]]
	return [{**newest, "kind": "new", "count": count, "names": names}]


def without_zeros(counts: dict) -> dict:
	return {key: count for key, count in counts.items() if count}


class TeamBrief(Brief):
	def __init__(self, user: str):
		self.scope = Team(user)
		self.doctype = brief_doctype(user)
		self.doctypes = DOCTYPES[self.doctype]

	def summary(self) -> dict:
		clients = RecentClientsWaiting(self.doctypes, self.scope)
		clients.row_limit = MORE_LIMIT
		rows = [{**row, "kind": "client"} for row in clients.rows()]
		ownerless = self.ownerless()
		if ownerless:
			past = [row for row in rows if row["past_response"]]
			rest = [row for row in rows if not row["past_response"]]
			rows = [*past, ownerless, *rest]
		people = [*self.workload(), *self.overdue_people()]
		total = clients.count() + bool(ownerless) + len(people)
		grouped = {"clients": rows, "people": people}
		shown = allocate(grouped, TEAM_SLOTS)
		set_last_emails(shown["clients"])
		items = [*shown["clients"], *shown["people"]]
		return {
			"items": items,
			"total": total,
			"more": more_records(grouped, shown),
			"older": self.older(),
		}

	def count(self) -> int:
		clients = RecentClientsWaiting(self.doctypes, self.scope).count()
		return clients + bool(self.ownerless()) + len(self.workload()) + len(self.overdue_people())

	def older_widgets(self) -> dict:
		return {
			"conversations": OlderRecords(
				ClientsWaiting(self.doctypes, self.scope), RecentClientsWaiting(self.doctypes, self.scope)
			),
			"tasks": OlderTasks(
				OverdueFollowUps(self.doctypes, self.scope), TeamOverdueFollowUps(self.doctypes, self.scope)
			),
		}

	def ownerless(self) -> dict | None:
		if "CRM Lead" not in self.doctypes:
			return None
		widget = Ownerless(("CRM Lead",), self.scope)
		count = widget.count()
		if not count:
			return None
		table = frappe.qb.DocType("CRM Lead")
		oldest = widget.query("CRM Lead", table).select(Min(table.creation)).run()[0][0]
		return {"kind": "ownerless", "count": count, "since": oldest}

	def overdue_people(self) -> list:
		widget = TeamOverdueFollowUps(self.doctypes, self.scope)
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

	def record_names(self, kind: str, doctype: str | None = None, member: str | None = None) -> list:
		"""Both lists are limited to the team's scope, so naming someone else's member finds nothing."""
		if kind == "behind":
			return member_names(self.behind_widget(), self.record_doctype(doctype), member)
		if kind == "overdue":
			widget = TeamOverdueFollowUps(self.doctypes, self.scope)
			task = widget.task
			return widget.query().select(task.name).where(task.assigned_to == member).run(pluck=True)
		return super().record_names(kind, doctype)

	def behind_widget(self) -> RecordWidget:
		widget = PastResponse if has_sla() else WaitingTooLong
		return widget(self.doctypes, self.scope)

	def workload(self) -> list:
		members = set(self.scope.members)
		behind_widget = self.behind_widget()
		by_doctype = member_counts_by_doctype(behind_widget)
		behind = sum(by_doctype.values(), Counter())
		behind = {member: count for member, count in behind.items() if member in members}
		if not behind:
			return []

		open_records = member_counts(RecordWidget(self.doctypes, self.scope))
		active = member_counts(RecentlyWorked(self.doctypes, self.scope))
		spare = [
			member
			for member in members - set(behind)
			if member != self.scope.user and open_records[member] and active[member]
		]
		lightest = min(spare, key=lambda member: (open_records[member], member), default=None)
		# A link opens one list, so it goes to the type holding most of the member's records.
		linked = {
			member: max(by_doctype, key=lambda doctype: by_doctype[doctype][member]) for member in behind
		}
		return [
			{
				"kind": "workload",
				"member": member,
				"behind": count,
				"doctype": RECORD_KEYS[linked[member]],
				"linked": by_doctype[linked[member]][member],
				"past_response": isinstance(behind_widget, PastResponse),
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


BRIEFS = {"mine": MineBrief, "team": TeamBrief}


def get_brief(user: str, tab: str | None = None) -> dict:
	"""The reply names its tab, so the page can tell a late reply for the other tab apart."""
	tab = tab or brief_tab(user)
	brief = brief_for(user, tab)
	return {**brief.summary(), "tab": tab, "doctype": brief.doctype}


def get_brief_count(user: str, tab: str) -> int:
	"""Asked for apart from the Brief, so the tab on screen does not wait for the other tab's count."""
	return brief_for(user, tab).count()


def get_brief_records(
	user: str, tab: str, kind: str, doctype: str | None = None, member: str | None = None
) -> list:
	"""The names behind a count in the brief, so its link can open a list of exactly those records."""
	return brief_for(user, tab).record_names(kind, doctype, member)


def brief_doctype(user: str) -> str:
	"""Lead, Deal or Both. Both is never saved, so a user who has not chosen sees everything."""
	return frappe.defaults.get_user_default(DOCTYPE_KEY, user) or "Both"


def set_brief_doctype(user: str, doctype: str):
	if doctype not in DOCTYPES:
		frappe.throw(_("The brief can only show Lead, Deal or Both"))
	if doctype == "Both":
		frappe.defaults.clear_user_default(DOCTYPE_KEY, user)
	else:
		frappe.defaults.set_user_default(DOCTYPE_KEY, doctype, user)


def brief_tab(user: str) -> str:
	"""A user who stops being a manager keeps the saved team tab, but can no longer read it."""
	tab = frappe.defaults.get_user_default(TAB_KEY, user)
	return "team" if tab == "team" and role_for(user) == "manager" else "mine"


def set_brief_tab(user: str, tab: str):
	brief_for(user, tab)
	if tab == "mine":
		frappe.defaults.clear_user_default(TAB_KEY, user)
	else:
		frappe.defaults.set_user_default(TAB_KEY, tab, user)


def brief_for(user: str, tab: str) -> MineBrief | TeamBrief:
	if tab not in BRIEFS:
		frappe.throw(_("Unknown brief tab {0}").format(tab))
	if tab == "team" and role_for(user) != "manager":
		frappe.throw(_("The team brief is only available to managers"), frappe.PermissionError)
	return BRIEFS[tab](user)
