import frappe
from frappe.query_builder.functions import Count

from crm.api.doc import COUNT_NAME
from crm.fcrm.doctype.crm_dashboard.home_layout import HomeLayout, RoleDefault
from crm.fcrm.doctype.crm_task.rules import FOLLOW_UP_DOCTYPES, TaskDue
from crm.utils import sales_user_only

LANDING_PAGE_KEY = "crm_landing_page"
OWNER_FIELDS = {"CRM Lead": "lead_owner", "CRM Deal": "deal_owner"}


@frappe.whitelist(methods=["POST"])
@sales_user_only
def set_landing_page(page: str | None = None):
	"""Store where `/` sends the user: Home (cleared), a page route name or a CRM View Settings name."""
	if not page or page == "Home":
		frappe.defaults.clear_user_default(LANDING_PAGE_KEY)
	else:
		frappe.defaults.set_user_default(LANDING_PAGE_KEY, page)


@frappe.whitelist()
@sales_user_only
def get_layout() -> dict:
	return HomeLayout().get()


@frappe.whitelist(methods=["POST"])
@sales_user_only
def save_layout(layout: list | str) -> dict:
	return HomeLayout().save(layout)


@frappe.whitelist(methods=["POST"])
@sales_user_only
def reset_layout() -> dict:
	return HomeLayout().reset()


@frappe.whitelist()
def get_default_layout(role: str) -> dict:
	frappe.only_for("System Manager")
	return RoleDefault(role).get()


@frappe.whitelist(methods=["POST"])
def save_default_layout(role: str, layout: list | str) -> dict:
	frappe.only_for("System Manager")
	return RoleDefault(role).save(layout)


@frappe.whitelist(methods=["POST"])
def reset_default_layout(role: str) -> dict:
	frappe.only_for("System Manager")
	return RoleDefault(role).reset()


@frappe.whitelist()
@sales_user_only
def get_counts() -> dict:
	user = frappe.session.user
	return {
		"replies_waiting": count_replies_waiting(user),
		"follow_ups_due": count_follow_ups_due(user),
		"new_leads": count_new_leads(user),
	}


def count_replies_waiting(user: str) -> int:
	waiting = {"awaiting_reply_since": ["is", "set"]}
	return count_mine("CRM Lead", user, {**waiting, "converted": 0}) + count_mine("CRM Deal", user, waiting)


def count_new_leads(user: str) -> int:
	open_statuses = frappe.get_all("CRM Lead Status", filters={"type": "Open"}, pluck="name")
	if not open_statuses:
		return 0
	return count_mine("CRM Lead", user, {"converted": 0, "status": ["in", open_statuses]})


def count_follow_ups_due(user: str) -> int:
	task = frappe.qb.DocType("CRM Task")
	query = (
		frappe.qb.from_(task)
		.select(Count("*"))
		.where(
			(task.assigned_to == user)
			& task.reference_doctype.isin(FOLLOW_UP_DOCTYPES)
			& task.reference_docname.isnotnull()
			& (task.reference_docname != "")
			& TaskDue(user).due_by_today_condition(task)
		)
	)
	return query.run()[0][0]


def count_mine(doctype: str, user: str, filters: dict) -> int:
	"""Count records assigned to or owned by `user`, within what they may read."""
	mine = [[doctype, "_assign", "like", f'%"{user}"%'], [doctype, OWNER_FIELDS[doctype], "=", user]]
	return frappe.get_list(doctype, filters=filters, or_filters=mine, fields=[COUNT_NAME])[0].total_count
