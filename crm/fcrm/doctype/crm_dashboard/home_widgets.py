# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Rows and totals for the shared Home widgets, always the viewer's own leads, deals and tasks.

Records are "mine" when owned by or assigned to the viewer. Every CRM permission rule
already lets a user read those, so the queries skip permission conditions and keep a
single selective predicate each.
"""

from dataclasses import dataclass
from datetime import timedelta

import frappe
from frappe import _
from frappe.query_builder import Case, Field, Order
from frappe.query_builder.functions import Coalesce, Count, Max
from frappe.utils import now_datetime
from pypika.terms import Function

from crm.fcrm.doctype.crm_dashboard.reply_channel import set_reply_channels
from crm.fcrm.doctype.crm_task.rules import CLOSED_STATUSES, FOLLOW_UP_DOCTYPES, TaskDue

ROW_LIMIT = 6
IDLE_DAYS = 7
UPCOMING_DAYS = 7
ACTIVE_STATUS_TYPES = ("Open", "Ongoing")
DOCTYPES = {"Lead": ("CRM Lead",), "Deal": ("CRM Deal",), "Both": FOLLOW_UP_DOCTYPES}


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


def get_widget_data(widget: str, doctype: str = "Both", user: str | None = None) -> dict:
	if widget not in WIDGET_DATA:
		frappe.throw(_("Home widget {0} has no data").format(widget))
	if doctype not in DOCTYPES:
		frappe.throw(_("Home widget {0} can only be set to Lead, Deal or Both").format(widget))
	data = WIDGET_DATA[widget](DOCTYPES[doctype], user or frappe.session.user)
	return {"rows": data.rows(), "total": data.count()}


class RecordWidget:
	"""Open or ongoing leads and deals of the user, merged across doctypes by `sort_field`."""

	sort_field = "modified"
	descending = False
	status_types = ACTIVE_STATUS_TYPES

	def __init__(self, doctypes: tuple, user: str):
		self.doctypes = doctypes
		self.user = user

	def rows(self) -> list:
		rows = []
		for doctype in self.doctypes:
			table = frappe.qb.DocType(doctype)
			query = self.query(doctype, table).select(*self.fields(doctype, table), self.sort_term(table))
			order = Order.desc if self.descending else Order.asc
			for row in query.orderby(Field(self.sort_field), order=order).limit(ROW_LIMIT).run(as_dict=True):
				rows.append({**row, "doctype": doctype})
		rows.sort(key=lambda row: row[self.sort_field], reverse=self.descending)
		return self.decorate(rows[:ROW_LIMIT])

	def count(self) -> int:
		return sum(self._count(doctype) for doctype in self.doctypes)

	def query(self, doctype: str, table):
		record_type = RECORD_TYPES[doctype]
		mine = table._assign.like(f'%"{self.user}"%') | (table[record_type.owner_field] == self.user)
		return self.active(doctype, table).where(mine)

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

	def query(self, doctype: str, table):
		return super().query(doctype, table).where(table.awaiting_reply_since.isnotnull())

	def fields(self, doctype: str, table) -> list:
		fields = super().fields(doctype, table)
		return [*fields, table.lead] if doctype == "CRM Deal" else fields

	def decorate(self, rows: list) -> list:
		set_reply_channels(rows)
		return rows


class NewLeads(RecordWidget):
	status_types = ("Open",)


class AssignedToMe(RecordWidget):
	"""Records with an open assignment to the user, newest assignment first.

	Owned records without an assignment are left out: the widget is about assignments.
	"""

	sort_field = "assigned_at"
	descending = True

	def query(self, doctype: str, table):
		todo = frappe.qb.DocType("ToDo")
		return (
			self.active(doctype, table)
			.join(todo)
			.on((todo.reference_type == doctype) & (todo.reference_name == table.name))
			.where((todo.allocated_to == self.user) & (todo.status == "Open"))
			.groupby(table.name)
		)

	def sort_term(self, table):
		return Max(frappe.qb.DocType("ToDo").creation).as_(self.sort_field)


class NoNextStep(RecordWidget):
	"""Records idle for IDLE_DAYS with no open task, longest idle first.

	Idle counts from the latest of `modified` and the last inbound or outbound message,
	because emails and calls record interactions without touching `modified`.
	"""

	sort_field = "idle_since"

	def query(self, doctype: str, table):
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
			.query(doctype, table)
			.where(idle_since(table) < cutoff)
			.where(table.name.notin(with_open_task))
		)

	def sort_term(self, table):
		return idle_since(table).as_(self.sort_field)


class TaskWidget:
	"""Open tasks assigned to the user."""

	FIELDS = ("name", "title", "status", "priority", "due_date", "all_day")

	def __init__(self, doctypes: tuple, user: str):
		self.doctypes = doctypes
		self.user = user
		self.task = frappe.qb.DocType("CRM Task")
		self.due = TaskDue(user)

	def rows(self) -> list:
		task = self.task
		query = self.query().select(*self.FIELDS, task.reference_doctype, task.reference_docname)
		rows = self.order(query).limit(ROW_LIMIT).run(as_dict=True)
		set_reference_titles(rows)
		return rows

	def count(self) -> int:
		return self.query().select(Count("*")).run()[0][0]

	def query(self):
		task = self.task
		return frappe.qb.from_(task).where((task.assigned_to == self.user) & self.condition())

	def linked(self):
		task = self.task
		return (
			task.reference_doctype.isin(self.doctypes)
			& task.reference_docname.isnotnull()
			& (task.reference_docname != "")
		)

	def order(self, query):
		return query.orderby(self.task.due_date)


class FollowUpsDue(TaskWidget):
	def condition(self):
		return self.linked() & self.due.due_by_today_condition(self.task)

	def order(self, query):
		overdue_first = Case().when(self.due.overdue_condition(self.task), 0).else_(1)
		return query.orderby(overdue_first).orderby(self.task.due_date)


class UpcomingFollowUps(TaskWidget):
	def condition(self):
		return self.linked() & self.due.upcoming_condition(self.task, UPCOMING_DAYS)


class MyTasks(TaskWidget):
	def condition(self):
		task = self.task
		standalone = task.reference_docname.isnull() | (task.reference_docname == "")
		return standalone & task.status.notin(CLOSED_STATUSES)

	def order(self, query):
		return (
			query.orderby(self.task.due_date.isnull())
			.orderby(self.task.due_date)
			.orderby(self.task.creation, order=Order.desc)
		)


WIDGET_DATA = {
	"replies_waiting": RepliesWaiting,
	"assigned_to_me": AssignedToMe,
	"no_next_step": NoNextStep,
	"follow_ups_due": FollowUpsDue,
	"upcoming_follow_ups": UpcomingFollowUps,
	"my_tasks": MyTasks,
}


def set_reference_titles(rows: list):
	names = {}
	for row in rows:
		if row.reference_doctype in RECORD_TYPES and row.reference_docname:
			names.setdefault(row.reference_doctype, []).append(row.reference_docname)

	titles = {}
	for doctype, docnames in names.items():
		title_field = RECORD_TYPES[doctype].title_field
		for record in frappe.get_all(doctype, {"name": ["in", docnames]}, ["name", title_field]):
			titles[doctype, record.name] = record[title_field] or record.name

	for row in rows:
		row.reference_title = titles.get((row.reference_doctype, row.reference_docname))


def idle_since(table):
	return Function(
		"GREATEST",
		table.modified,
		Coalesce(table.last_inbound_at, table.modified),
		Coalesce(table.last_outbound_at, table.modified),
	)
