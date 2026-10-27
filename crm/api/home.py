import frappe
from frappe import _

from crm.api.digest import OPT_OUT_KEY
from crm.fcrm.doctype.crm_dashboard.home_layout import (
	WIDGETS,
	HomeLayout,
	RoleDefault,
	role_for,
	widget_columns,
)
from crm.fcrm.doctype.crm_dashboard.home_scope import Mine, Team
from crm.fcrm.doctype.crm_dashboard.home_widgets import (
	DOCTYPES,
	WIDGET_DATA,
	FollowUpsDue,
	NewLeads,
	RepliesWaiting,
)
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
def get_widget(widget: str, doctype: str = "Both", columns: list | str | None = None) -> dict:
	return get_widget_data(widget, doctype, columns=frappe.parse_json(columns) if columns else None)


@frappe.whitelist()
@sales_user_only
def get_widget_columns(widget: str, doctype: str = "Both") -> dict:
	"""Fields the user can add as columns to `widget`, and the columns they cannot remove."""
	validate_widget(widget, doctype)
	columns = widget_columns(widget, {"doctype": doctype})
	return {"fields": columns.available(), "locked": WIDGETS[widget].locked}


def get_widget_data(
	widget: str, doctype: str = "Both", user: str | None = None, columns: list | None = None
) -> dict:
	user = user or frappe.session.user
	if widget not in WIDGET_DATA and widget not in TEAM_WIDGET_DATA:
		frappe.throw(_("Home widget {0} has no data").format(widget))
	validate_widget(widget, doctype)
	extra = widget_columns(widget, {"doctype": doctype}, user).extra(columns)

	if widget in WIDGET_DATA:
		return WIDGET_DATA[widget](DOCTYPES[doctype], Mine(user), extra).summary()
	if role_for(user) != "manager":
		frappe.throw(
			_("Home widget {0} is only available to managers").format(widget), frappe.PermissionError
		)
	return TEAM_WIDGET_DATA[widget](DOCTYPES[doctype], Team(user), extra).summary()


def validate_widget(widget: str, doctype: str):
	if widget not in WIDGETS:
		frappe.throw(_("Unknown Home widget {0}").format(widget))
	if doctype not in DOCTYPES:
		frappe.throw(_("Home widget {0} can only be set to Lead, Deal or Both").format(widget))
