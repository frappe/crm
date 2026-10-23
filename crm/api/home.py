import frappe

from crm.fcrm.doctype.crm_dashboard.home_layout import HomeLayout, RoleDefault
from crm.fcrm.doctype.crm_dashboard.home_scope import Mine
from crm.fcrm.doctype.crm_dashboard.home_widgets import (
	FollowUpsDue,
	NewLeads,
	RepliesWaiting,
	get_widget_data,
)
from crm.fcrm.doctype.crm_task.rules import FOLLOW_UP_DOCTYPES
from crm.utils import sales_user_only

LANDING_PAGE_KEY = "crm_landing_page"


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
	mine = Mine(frappe.session.user)
	return {
		"replies_waiting": RepliesWaiting(FOLLOW_UP_DOCTYPES, mine).count(),
		"follow_ups_due": FollowUpsDue(FOLLOW_UP_DOCTYPES, mine).count(),
		"new_leads": NewLeads(("CRM Lead",), mine).count(),
	}


@frappe.whitelist()
@sales_user_only
def get_widget(widget: str, doctype: str = "Both") -> dict:
	return get_widget_data(widget, doctype)
