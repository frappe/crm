# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# GNU GPLv3 License. See license.txt

import frappe
from frappe import _
from frappe.integrations.frappe_providers.frappecloud_billing import is_fc_site
from frappe.translate import get_messages_for_boot, get_translated_doctypes
from frappe.utils import cint, get_system_timezone
from frappe.utils.telemetry import capture

no_cache = 1


def get_context():
	from crm.api import check_app_permission

	if not check_app_permission():
		frappe.throw(_("You do not have permission to access Frappe CRM"), frappe.PermissionError)

	frappe.db.commit()
	context = frappe._dict()
	context.boot = get_boot()
	if frappe.session.user != "Guest":
		capture("active_site", "crm")
	return context


@frappe.whitelist(methods=["POST"], allow_guest=True)
def get_context_for_dev():
	if not frappe.conf.developer_mode:
		frappe.throw(_("This method is only meant for developer mode"))
	return get_boot()


def get_boot():
	return frappe._dict(
		{
			"frappe_version": frappe.__version__,
			"default_route": get_default_route(),
			"site_name": frappe.local.site,
			"socketio_port": frappe.conf.socketio_port,
			"read_only_mode": frappe.flags.read_only,
			"csrf_token": frappe.sessions.get_csrf_token(),
			"setup_complete": cint(frappe.get_system_settings("setup_complete")),
			"sysdefaults": frappe.defaults.get_defaults(),
			"is_demo_site": frappe.conf.get("is_demo_site"),
			"demo_data_created": frappe.db.get_default("crm_demo_data_created") == "1",
			"is_fc_site": is_fc_site(),
			"show_sales_hierarchy_banner": frappe.db.count("CRM Lead") > 0,
			"translated_doctypes": get_translated_doctypes(),
			"translated_messages": get_messages_for_boot(),
			"timezone": {
				"system": get_system_timezone(),
				"user": frappe.db.get_value("User", frappe.session.user, "time_zone")
				or get_system_timezone(),
			},
			"state_options": get_state_options(),
		}
	)


def get_state_options() -> dict[str, list[str]]:
	"""Country -> list of states, so the frontend can render a state dropdown.

	Sourced from India Compliance's own constant when that app is installed, so the
	options stay in sync with the desk. Returns an empty map (state field stays free
	text) on any failure.

	This runs inside ``get_boot``, so it must never raise — a failure here would break
	the whole CRM page load. ``frappe.get_installed_apps`` can return `[]` or raise in
	unauthenticated/boot contexts (notably on v15), so the lookup is wrapped defensively.
	"""
	try:
		if "india_compliance" not in frappe.get_installed_apps():
			return {}

		from india_compliance.gst_india.constants import INDIAN_STATES

		return {"India": list(INDIAN_STATES)}
	except Exception:
		# Degrade silently to free-text: this runs in boot, so the except branch
		# must not do anything that can itself raise (e.g. logging to a missing dir).
		return {}


def get_default_route():
	return "/crm"
