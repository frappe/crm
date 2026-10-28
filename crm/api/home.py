import frappe
from frappe import _

from crm.api.digest import OPT_OUT_KEY
from crm.fcrm.doctype.crm_dashboard.home_layout import (
	DEFAULT_PERIOD,
	WIDGETS,
	HomeLayout,
	RoleDefault,
	role_for,
)
from crm.fcrm.doctype.crm_dashboard.home_scope import Mine, Team
from crm.fcrm.doctype.crm_dashboard.home_widgets import (
	DOCTYPES,
	TABBED_WIDGETS,
	WIDGET_DATA,
	FollowUpsDue,
	NewLeads,
	RepliesWaiting,
)
from crm.fcrm.doctype.crm_dashboard.recent_activity import RecentActivity
from crm.fcrm.doctype.crm_dashboard.sales_widgets import SALES_WIDGET_DATA
from crm.fcrm.doctype.crm_dashboard.team_widgets import TEAM_WIDGET_DATA
from crm.fcrm.doctype.crm_task.rules import FOLLOW_UP_DOCTYPES
from crm.utils import sales_user_only

LANDING_PAGE_KEY = "crm_landing_page"


@frappe.whitelist(methods=["POST"])
@sales_user_only
def set_landing_page(page: str | None = None):
	"""`page` is a page route name or a CRM View Settings name."""
	if not page or page == "Home":
		frappe.defaults.clear_user_default(LANDING_PAGE_KEY)
	else:
		frappe.defaults.set_user_default(LANDING_PAGE_KEY, page)


@frappe.whitelist(methods=["POST"])
@sales_user_only
def set_morning_digest(enabled: bool):
	if enabled:
		frappe.defaults.clear_user_default(OPT_OUT_KEY)
	else:
		frappe.defaults.set_user_default(OPT_OUT_KEY, "0")


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
def get_tab(widget: str, tab: str, doctype: str = "Both") -> dict:
	return get_tab_data(widget, tab, doctype)


@frappe.whitelist()
@sales_user_only
def get_widget(widget: str, doctype: str = "Both", period: str | None = None) -> dict:
	return get_widget_data(widget, doctype, period=period)


def get_widget_data(
	widget: str, doctype: str = "Both", user: str | None = None, period: str | None = None
) -> dict:
	user = user or frappe.session.user
	shared = {**WIDGET_DATA, **SALES_WIDGET_DATA, "recently_opened": RecentActivity}
	if widget not in shared and widget not in TEAM_WIDGET_DATA:
		frappe.throw(_("Home widget {0} has no data").format(widget))
	if doctype not in DOCTYPES:
		frappe.throw(_("Home widget {0} can only be set to Lead, Deal or Both").format(widget))

	if widget in SALES_WIDGET_DATA:
		return SALES_WIDGET_DATA[widget](DOCTYPES[doctype], Mine(user), period or DEFAULT_PERIOD).summary()
	if widget in shared:
		return shared[widget](DOCTYPES[doctype], Mine(user)).summary()
	if role_for(user) != "manager":
		frappe.throw(
			_("Home widget {0} is only available to managers").format(widget), frappe.PermissionError
		)
	args = (DOCTYPES[doctype], Team(user))
	if WIDGETS[widget].period_setting:
		args += (period or DEFAULT_PERIOD,)
	return TEAM_WIDGET_DATA[widget](*args).summary()


def get_tab_data(widget: str, tab: str, doctype: str = "Both", user: str | None = None) -> dict:
	if widget not in TABBED_WIDGETS:
		frappe.throw(_("Home widget {0} has no tabs").format(widget))
	if doctype not in DOCTYPES:
		frappe.throw(_("Home widget {0} can only be set to Lead, Deal or Both").format(widget))
	return TABBED_WIDGETS[widget](DOCTYPES[doctype], Mine(user or frappe.session.user), tab).summary()
