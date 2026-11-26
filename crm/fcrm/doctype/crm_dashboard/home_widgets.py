# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import ClassVar

import frappe
from frappe import _
from frappe.query_builder import Case, Field, Order
from frappe.query_builder.functions import Coalesce, Count, Max
from frappe.utils import now_datetime
from pypika.terms import Function

from crm.fcrm.doctype.crm_dashboard.home_scope import Mine, Team
from crm.fcrm.doctype.crm_dashboard.reply_channel import set_reply_channels
from crm.fcrm.doctype.crm_task.rules import CLOSED_STATUSES, FOLLOW_UP_DOCTYPES, TaskDue

ROW_LIMIT = 6
IDLE_DAYS = 7
UPCOMING_DAYS = 7
ACTIVE_STATUS_TYPES = ("Open", "Ongoing")
DOCTYPES = {"Lead": ("CRM Lead",), "Deal": ("CRM Deal",), "Both": FOLLOW_UP_DOCTYPES}


def check_filters(doctypes: tuple, filters):
	"""Only columns every doctype has, so a filter cannot reach into a linked table."""
	if not isinstance(filters, dict):
		frappe.throw(_("Team workload filters must name a field and a value"))
	for doctype in doctypes:
		unknown = set(filters) - set(frappe.db.get_table_columns(doctype))
		if unknown:
			frappe.throw(
				_("Team workload cannot filter {0} on {1}").format(_(doctype), ", ".join(sorted(unknown)))
			)


@dataclass(frozen=True)
class RecordType:
	owner_field: str
	status_doctype: str
	title_field: str
	subtitle_field: str


RECORD_TYPES = {
	"CRM Lead": RecordType("lead_owner", "CRM Lead Status", "lead_name", "organization"),
	"CRM Deal": RecordType("deal_owner", "CRM Deal Status", "organization", "lead_name"),
}


class Widget:
	row_limit = ROW_LIMIT

	def __init__(self, doctypes: tuple, scope: Mine | Team):
		self.doctypes = doctypes
		self.scope = scope

	def summary(self) -> dict:
		return {"rows": self.rows(), "total": self.count()}


class RecordWidget(Widget):
	sort_field = "modified"
	descending = False
	status_types = ACTIVE_STATUS_TYPES

	def rows(self) -> list:
		rows = []
		order = Order.desc if self.descending else Order.asc
		for doctype in self.doctypes:
			table = frappe.qb.DocType(doctype)
			query = self.query(doctype, table).select(*self.fields(doctype, table), self.sort_term(table))
			for row in (
				query.orderby(Field(self.sort_field), order=order).limit(self.row_limit).run(as_dict=True)
			):
				rows.append({**row, "doctype": doctype})
		rows.sort(key=lambda row: row[self.sort_field], reverse=self.descending)
		return self.decorate(rows[: self.row_limit])

	def count(self) -> int:
		return sum(self._count(doctype) for doctype in self.doctypes)

	def query(self, doctype: str, table):
		in_scope = self.scope.records(doctype, table, RECORD_TYPES[doctype].owner_field)
		return self.filtered(doctype, table).where(in_scope)

	def filtered(self, doctype: str, table):
		return self.active(doctype, table)

	def active(self, doctype: str, table):
		status = frappe.qb.DocType(RECORD_TYPES[doctype].status_doctype)
		active_statuses = (
			frappe.qb.from_(status).select(status.name).where(status.type.isin(self.status_types))
		)
		query = frappe.qb.from_(table).where(table.status.isin(active_statuses))
		if doctype == "CRM Lead":
			# a converted lead is represented by its deal
			query = query.where(table.converted == 0)
		return query

	def fields(self, doctype: str, table) -> list:
		record_type = RECORD_TYPES[doctype]
		return [
			table.name,
			table.status,
			table[record_type.title_field].as_("title"),
			table[record_type.subtitle_field].as_("subtitle"),
		]

	def sort_term(self, table):
		return table[self.sort_field]

	def decorate(self, rows: list) -> list:
		return rows

	def _count(self, doctype: str) -> int:
		table = frappe.qb.DocType(doctype)
		query = self.query(doctype, table).select(table.name)
		return frappe.qb.from_(query).select(Count("*")).run()[0][0]


class RepliesWaiting(RecordWidget):
	sort_field = "awaiting_reply_since"

	def filtered(self, doctype: str, table):
		return super().filtered(doctype, table).where(table.awaiting_reply_since.isnotnull())

	def fields(self, doctype: str, table) -> list:
		fields = super().fields(doctype, table)
		return [*fields, table.lead] if doctype == "CRM Deal" else fields

	def decorate(self, rows: list) -> list:
		set_reply_channels(rows)
		return rows


class NewLeads(RecordWidget):
	status_types = ("Open",)
	sort_field = "creation"
	descending = True


class AssignedToMe(RecordWidget):
	"""Unlike Mine, owned records without an open assignment are left out."""

	sort_field = "assigned_at"
	descending = True

	def query(self, doctype: str, table):
		todo = frappe.qb.DocType("ToDo")
		return (
			self.active(doctype, table)
			.join(todo)
			.on((todo.reference_type == doctype) & (todo.reference_name == table.name))
			.where((todo.allocated_to == self.scope.user) & (todo.status == "Open"))
			.groupby(table.name)
		)

	def sort_term(self, table):
		return Max(frappe.qb.DocType("ToDo").creation).as_(self.sort_field)


class NoNextStep(RecordWidget):
	sort_field = "idle_since"

	def filtered(self, doctype: str, table):
		task = frappe.qb.DocType("CRM Task")
		with_open_task = (
			frappe.qb.from_(task)
			.select(task.reference_docname)
			.where(
				(task.reference_doctype == doctype)
				& task.reference_docname.isnotnull()
				& task.status.notin(CLOSED_STATUSES)
			)
		)
		cutoff = now_datetime() - timedelta(days=IDLE_DAYS)
		return (
			super()
			.filtered(doctype, table)
			.where(idle_since(table) < cutoff)
			.where(table.name.notin(with_open_task))
		)

	def sort_term(self, table):
		return idle_since(table).as_(self.sort_field)


class TaskWidget(Widget):
	FIELDS = ("name", "title", "status", "priority", "due_date", "all_day")

	def __init__(self, doctypes: tuple, scope: Mine | Team):
		super().__init__(doctypes, scope)
		self.task = frappe.qb.DocType("CRM Task")
		self.due = TaskDue(scope.user)

	def rows(self) -> list:
		task = self.task
		query = self.query().select(*self.FIELDS, task.reference_doctype, task.reference_docname)
		rows = self.order(query).limit(self.row_limit).run(as_dict=True)
		set_reference_titles(rows, self.scope.user)
		return rows

	def count(self) -> int:
		return self.query().select(Count("*")).run()[0][0]

	def query(self):
		task = self.task
		return frappe.qb.from_(task).where(self.scope.tasks(task) & self.condition())

	def linked(self):
		task = self.task
		return (
			task.reference_doctype.isin(self.doctypes)
			& task.reference_docname.isnotnull()
			& (task.reference_docname != "")
		)

	def standalone(self):
		task = self.task
		return task.reference_docname.isnull() | (task.reference_docname == "")

	def order(self, query):
		return query.orderby(self.task.due_date)


class OpenTasks(TaskWidget):
	def condition(self):
		return self.task.status.notin(CLOSED_STATUSES)

	def order(self, query):
		return (
			query.orderby(self.task.due_date.isnull())
			.orderby(self.task.due_date)
			.orderby(self.task.creation, order=Order.desc)
		)


class DueTasks(TaskWidget):
	def condition(self):
		return self.due.due_by_today_condition(self.task)

	def order(self, query):
		overdue_first = Case().when(self.due.overdue_condition(self.task), 0).else_(1)
		return query.orderby(overdue_first).orderby(self.task.due_date)


class FollowUpsDue(DueTasks):
	def condition(self):
		return self.linked() & super().condition()

	def order(self, query):
		"""High priority comes first, even when it is due later than an overdue task."""
		high_first = Case().when(self.task.priority == "High", 0).else_(1)
		return query.orderby(high_first).orderby(self.task.due_date)


class UpcomingTasks(TaskWidget):
	def condition(self):
		return self.due.upcoming_condition(self.task, UPCOMING_DAYS)


class UnlinkedTasks(OpenTasks):
	def condition(self):
		return self.standalone() & super().condition()


class TodaysMeetings(Widget):
	"""Events the user hosts or attends today, in the user's time zone."""

	row_limit = 50
	FIELDS = (
		"name",
		"subject",
		"starts_on",
		"ends_on",
		"all_day",
		"color",
		"owner",
		"location",
		"google_meet_link",
	)

	def __init__(self, doctypes: tuple, scope: Mine | Team):
		super().__init__(doctypes, scope)
		self.event = frappe.qb.DocType("Event")
		self.due = TaskDue(scope.user)

	def rows(self) -> list:
		event = self.event
		query = self.query().select(*self.FIELDS)
		rows = (
			query.orderby(event.all_day, order=Order.desc)
			.orderby(event.starts_on)
			.limit(self.row_limit)
			.run(as_dict=True)
		)
		set_attendees(rows, self.scope.user)
		return rows

	def count(self) -> int:
		return self.query().select(Count("*")).run()[0][0]

	def query(self):
		event = self.event
		participant = frappe.qb.DocType("Event Participants")
		attending = (
			frappe.qb.from_(participant)
			.select(participant.parent)
			.where((participant.parenttype == "Event") & (participant.email == self.scope.user))
		)
		today = self.due.today
		tomorrow = today + timedelta(days=1)
		ends_on = Coalesce(event.ends_on, event.starts_on)
		timed = (
			(event.all_day == 0)
			& (event.starts_on < self.due._day_start(tomorrow))
			& (ends_on >= self.due._day_start(today))
		)
		# all-day events hold their dates as is, not shifted to system time
		all_day = (
			(event.all_day == 1)
			& (event.starts_on < datetime.combine(tomorrow, time.min))
			& (ends_on >= datetime.combine(today, time.min))
		)
		return frappe.qb.from_(event).where(
			(event.status != "Cancelled")
			& ((event.owner == self.scope.user) | event.name.isin(attending))
			& (timed | all_day)
		)


def set_attendees(rows: list, user: str):
	"""Everyone else in each meeting, its host first, named from their user or contact."""
	emails = {}
	for participant in frappe.get_all(
		"Event Participants",
		filters={"parenttype": "Event", "parent": ["in", [row.name for row in rows] or [""]]},
		fields=["parent", "email"],
		order_by="idx",
	):
		if participant.email:
			emails.setdefault(participant.parent, []).append(participant.email)

	people = {}
	everyone = {email for row in rows for email in [row.owner, *emails.get(row.name, [])]}
	for person in frappe.get_all(
		"User",
		filters={"name": ["in", list(everyone) or [""]]},
		fields=["name", "full_name", "user_image"],
	):
		people[person.name] = {"email": person.name, "name": person.full_name, "image": person.user_image}
	for contact in frappe.get_all(
		"Contact",
		filters={"email_id": ["in", list(everyone - set(people)) or [""]]},
		fields=["email_id", "full_name", "image"],
	):
		people.setdefault(
			contact.email_id, {"email": contact.email_id, "name": contact.full_name, "image": contact.image}
		)

	for row in rows:
		others = dict.fromkeys(e for e in [row.owner, *emails.get(row.name, [])] if e != user)
		row.attendees = [people.get(email) or {"email": email, "name": email} for email in others]
		row.pop("owner")


class TabbedWidget(Widget):
	TABS: ClassVar[dict] = {}

	def __init__(self, doctypes: tuple, scope: Mine, tab: str):
		if tab not in self.TABS:
			frappe.throw(_("Unknown tab {0}").format(tab))
		super().__init__(doctypes, scope)
		self.tabs = {key: widget(doctypes, scope) for key, widget in self.TABS.items()}
		self.tab = tab

	def summary(self) -> dict:
		counts = {key: widget.count() for key, widget in self.tabs.items()}
		return {"rows": self.tabs[self.tab].rows(), "total": counts[self.tab], "counts": counts}


class Tasks(TabbedWidget):
	TABS: ClassVar[dict] = {
		"all": OpenTasks,
		"due": DueTasks,
		"upcoming": UpcomingTasks,
		"unlinked": UnlinkedTasks,
	}


class LeadsAndDeals(TabbedWidget):
	TABS: ClassVar[dict] = {"replies": RepliesWaiting, "new": NewLeads}


WIDGET_DATA = {
	"no_next_step": NoNextStep,
	"todays_meetings": TodaysMeetings,
}

TABBED_WIDGETS = {"tasks": Tasks, "leads_and_deals": LeadsAndDeals}


def set_reference_titles(rows: list, user: str):
	"""A task can be on a record its assignee cannot read; that record gets no title."""
	names = {}
	for row in rows:
		if row.reference_doctype in RECORD_TYPES and row.reference_docname:
			names.setdefault(row.reference_doctype, []).append(row.reference_docname)

	titles = {}
	for doctype, docnames in names.items():
		title_field = RECORD_TYPES[doctype].title_field
		for record in frappe.get_list(
			doctype, filters={"name": ["in", docnames]}, fields=["name", title_field], user=user
		):
			titles[doctype, record.name] = record[title_field] or record.name

	for row in rows:
		row.reference_title = titles.get((row.reference_doctype, row.reference_docname))


def idle_since(table):
	"""Emails and calls record interactions without touching `modified`."""
	return Function(
		"GREATEST",
		table.modified,
		Coalesce(table.last_inbound_at, table.modified),
		Coalesce(table.last_outbound_at, table.modified),
	)
