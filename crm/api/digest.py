# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from datetime import timedelta

import frappe
from frappe import _
from frappe.email.doctype.email_account.email_account import EmailAccount
from frappe.query_builder.functions import Coalesce
from frappe.utils import (
	create_batch,
	format_date,
	format_time,
	get_datetime,
	get_url,
	now_datetime,
	pretty_date,
)

from crm.extends.notification_log import CRM_ROUTES
from crm.fcrm.doctype.crm_dashboard.brief import RecentFollowUpsDue, WaitingOnMe, brief_doctype
from crm.fcrm.doctype.crm_dashboard.home_scope import Mine, sales_users
from crm.fcrm.doctype.crm_dashboard.home_widgets import DOCTYPES, AssignedToMe, TaskWidget
from crm.fcrm.doctype.crm_task.rules import TaskDue

DIGEST_HOUR = 8
COUNT_CAP = 500
CUTOFF_HOUR = 11
BATCH_SIZE = 50
ASSIGNED_MAX_DAYS = 7
LAST_RUN_KEY = "crm_digest_last_run"
OPT_OUT_KEY = "crm_morning_digest"
CHANNEL_TABS = {"email": "emails", "whatsapp": "whatsapp"}


def send_morning_digests():
	if not frappe.db.get_single_value("FCRM Settings", "enable_morning_digest"):
		return
	# Without a sender every digest would fail, once per user per hour.
	if not has_outgoing_email_account():
		frappe.logger("crm").warning("Morning digest skipped: no default outgoing email account")
		return
	for batch in create_batch(sales_users(), BATCH_SIZE):
		frappe.enqueue(send_digests, queue="long", users=batch, now=frappe.flags.in_test)


@frappe.whitelist()
def has_outgoing_email_account() -> bool:
	"""The digest names no sender, so it needs a default outgoing account or mail settings in site config."""
	return bool(EmailAccount.find_outgoing())


def send_digests(users: list):
	for user in users:
		frappe.db.savepoint("morning_digest")
		try:
			digest = MorningDigest(user)
			if digest.is_due():
				digest.send()
		except Exception:
			frappe.db.rollback(save_point="morning_digest")
			frappe.log_error(title=f"CRM morning digest failed for {user}")


def is_opted_out(user: str) -> bool:
	return frappe.defaults.get_user_default(OPT_OUT_KEY, user) == "0"


class MorningDigest:
	def __init__(self, user: str, now=None):
		self.user = user
		self.now = now or now_datetime()
		self.due = TaskDue(user, self.now)
		self.local_now = self.due.user_time(self.now)

	def is_due(self) -> bool:
		if is_opted_out(self.user) or not DIGEST_HOUR <= self.local_now.hour < CUTOFF_HOUR:
			return False
		last_run = self.last_run()
		return not last_run or self.due.user_time(last_run).date() < self.local_now.date()

	def send(self):
		sections = self.sections()
		if any(section.total for section in sections):
			frappe.sendmail(
				recipients=frappe.db.get_value("User", self.user, "email"),
				subject=self.subject(sections),
				template="crm_morning_digest",
				args={
					"first_name": frappe.db.get_value("User", self.user, "first_name"),
					"date": format_date(self.local_now.date(), "EEEE, d MMMM"),
					"sections": sections,
					"home_url": get_url("/crm"),
				},
			)
		frappe.defaults.set_user_default(LAST_RUN_KEY, str(self.now), self.user)

	def sections(self) -> list:
		"""The same records as the user's brief on Home: their choice of leads or deals, and the last 30 days."""
		mine = Mine(self.user)
		doctypes = DOCTYPES[brief_doctype(self.user)]
		return [
			section.build()
			for section in (
				FollowUpsSection(doctypes, mine),
				RepliesSection(doctypes, mine),
				NewlyAssignedSection(doctypes, mine, self.assigned_since()),
				TasksDueTodaySection(doctypes, mine),
			)
		]

	def subject(self, sections: list) -> str:
		follow_ups, replies = sections[0].total, sections[1].total
		parts = []
		if follow_ups:
			parts.append(
				_("1 follow-up") if follow_ups == 1 else _("{0} follow-ups").format(capped(follow_ups))
			)
		if replies:
			parts.append(
				_("1 reply waiting") if replies == 1 else _("{0} replies waiting").format(capped(replies))
			)
		if not parts:
			return _("Your CRM morning")
		return _("Your CRM morning: {0}").format(", ".join(parts))

	def last_run(self):
		value = frappe.defaults.get_user_default(LAST_RUN_KEY, self.user)
		return get_datetime(value) if value else None

	def assigned_since(self):
		floor = self.now - timedelta(days=ASSIGNED_MAX_DAYS)
		last_run = self.last_run()
		return max(last_run, floor) if last_run else self.now - timedelta(days=1)


class Section:
	def build(self) -> frappe._dict:
		summary = self.summary()
		items = [self.item(row) for row in summary["rows"]]
		return frappe._dict(
			title=self.title(), items=items, total=summary["total"], more=summary["total"] - len(items)
		)

	def title(self) -> str:
		raise NotImplementedError

	def item(self, row) -> dict:
		raise NotImplementedError


class FollowUpsSection(Section, RecentFollowUpsDue):
	def title(self) -> str:
		return _("Follow-ups due")

	def item(self, row) -> dict:
		return {
			"title": row.title,
			"detail": joined(row.reference_title, due_label(self.due, row)),
			"url": record_url(row.reference_doctype, row.reference_docname, "tasks"),
			"overdue": self.due.is_overdue(row),
		}


class RepliesSection(Section, WaitingOnMe):
	def title(self) -> str:
		return _("Replies waiting")

	def item(self, row) -> dict:
		received = _("received {0}").format(pretty_date(row["awaiting_reply_since"]))
		channel = {"email": _("Email"), "whatsapp": _("WhatsApp")}.get(row["channel"])
		return {
			"title": row["title"] or row["name"],
			"detail": joined(row["subtitle"], channel, received),
			"url": record_url(row["doctype"], row["name"], CHANNEL_TABS.get(row["channel"])),
		}


class NewlyAssignedSection(Section, AssignedToMe):
	def __init__(self, doctypes: tuple, scope: Mine, since):
		super().__init__(doctypes, scope)
		self.since = since

	def title(self) -> str:
		return _("Newly assigned to you")

	def query(self, doctype: str, table):
		todo = frappe.qb.DocType("ToDo")
		return (
			super()
			.query(doctype, table)
			.where(todo.creation > self.since)
			.where(Coalesce(todo.assigned_by, "") != self.scope.user)
		)

	def item(self, row) -> dict:
		return {
			"title": row["title"] or row["name"],
			"detail": joined(row["subtitle"], row["status"]),
			"url": record_url(row["doctype"], row["name"]),
		}


class TasksDueTodaySection(Section, TaskWidget):
	def title(self) -> str:
		return _("Tasks due today")

	def condition(self):
		return self.standalone() & self.due.due_by_today_within_condition(self.task, 0)

	def item(self, row) -> dict:
		return {"title": row.title, "detail": due_label(self.due, row), "url": get_url("/crm/tasks")}


def capped(count: int) -> int | str:
	"""Past a few hundred the exact number means nothing to the reader, as on Home."""
	return f"{COUNT_CAP}+" if count > COUNT_CAP else count


def due_label(due: TaskDue, task) -> str:
	if due.is_overdue(task):
		day = get_datetime(task.due_date).date() if task.all_day else due.user_time(task.due_date).date()
		return _("Overdue since {0}").format(format_date(day, "d MMM"))
	if task.all_day:
		return _("Due today")
	return _("Due at {0}").format(format_time(due.user_time(task.due_date), "HH:mm"))


def joined(*parts) -> str:
	return " · ".join(part for part in parts if part)


def record_url(doctype: str, name: str, tab: str | None = None) -> str:
	return get_url(f"/crm/{CRM_ROUTES[doctype]}/{name}" + (f"#{tab}" if tab else ""))
