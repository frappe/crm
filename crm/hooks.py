import logging as _logging

_HOOKS_LOGGER = _logging.getLogger(__name__)


def _apply_queue_builder_patches_safely():
	try:
		from crm.email.queue_patch import apply_queue_builder_patches

		apply_queue_builder_patches()
	except Exception:
		_HOOKS_LOGGER.exception("Failed to apply SES QueueBuilder patches during hook import")


_apply_queue_builder_patches_safely()

app_name = "crm"
app_title = "Frappe CRM"
app_publisher = "Frappe Technologies Pvt. Ltd."
app_description = "Kick-ass Open Source CRM"
app_email = "shariq@frappe.io"
app_license = "AGPLv3"
app_icon_url = "/assets/crm/images/logo.svg"
app_icon_title = "CRM"
app_icon_route = "/crm"

# Apps
# ------------------

# required_apps = []
add_to_apps_screen = [
	{
		"name": "crm",
		"logo": "/assets/crm/images/logo.svg",
		"title": "CRM",
		"route": "/crm",
		"has_permission": "crm.api.check_app_permission",
	}
]

get_site_info = "crm.activation.get_site_info"

export_python_type_annotations = True
require_type_annotated_api_methods = True

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/crm/css/crm.css"
# app_include_js = "/assets/crm/js/crm.js"

# include js, css files in header of web template
# web_include_css = "/assets/crm/css/crm.css"
# web_include_js = "/assets/crm/js/crm.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "crm/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Sales Order": "public/js/erpnext_sales_order_customer.js",
	"CRM Lead": "public/js/domain_enrichment.js",
	"CRM Organization": "public/js/domain_enrichment.js",
	"CRM Deal": "public/js/domain_enrichment.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# Tiberbu CRM (E2-S1): public landing page at site root. `home_page` overrides Website
# Settings (verified: frappe website/utils.py get_home_page). Guests -> /index (branded
# landing); logged-in users are bounced to /crm by index.py before workspace resolution.
home_page = "index"

# website user home page (by Role)
# role_home_page = {
# "Role": "home_page"
# }

website_route_rules = [
	{"from_route": "/crm/<path:app_path>", "to_route": "crm"},
	{"from_route": "/crm-form/<route>", "to_route": "crm_form"},
	# E2-S1: route /login to the branded login page (shadows stock login *page* only;
	# the /api/method/login *method* is untouched).
	{"from_route": "/login", "to_route": "login"},
]

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# "methods": "crm.utils.jinja_methods",
# "filters": "crm.utils.jinja_filters"
# }

# Setup wizard
# setup_wizard_requires = "assets/crm/js/setup_wizard.js"
# setup_wizard_stages = "crm.setup.setup_wizard.setup_wizard.get_setup_stages"
setup_wizard_complete = "crm.demo.api.create_demo_data"
# setup_wizard_test = "crm.setup.setup_wizard.test_setup_wizard.run_setup_wizard_test"

# Installation
# ------------

before_install = "crm.install.before_install"
after_install = "crm.install.after_install"

# Uninstallation
# ------------

before_uninstall = "crm.uninstall.before_uninstall"
# after_uninstall = "crm.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "crm.utils.before_app_install"
# after_app_install = "crm.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "crm.utils.before_app_uninstall"
# after_app_uninstall = "crm.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "crm.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"CRM Lead": "crm.permissions.org_hierarchy.get_lead_permission_query_conditions",
	"CRM Deal": "crm.permissions.org_hierarchy.get_deal_permission_query_conditions",
	"CRM Notification": "crm.fcrm.doctype.crm_notification.crm_notification.get_permission_query_conditions",
	"CRM Pre-Qualified Facility": "crm.permissions.pre_qualified.get_permission_query",
}

has_permission = {
	"CRM Lead": "crm.permissions.org_hierarchy.has_lead_permission",
	"CRM Deal": "crm.permissions.org_hierarchy.has_deal_permission",
	"CRM Notification": "crm.fcrm.doctype.crm_notification.crm_notification.has_permission",
}

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Contact": "crm.overrides.contact.CustomContact",
	"Email Template": "crm.overrides.email_template.CustomEmailTemplate",
	"Email Queue": "crm.email.email_queue.CrmSesAwareEmailQueue",
}

override_email_send = "crm.email.ses_send.send"

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Contact": {
		"validate": ["crm.api.contact.validate"],
	},
	"ToDo": {
		"after_insert": ["crm.api.todo.after_insert"],
		"on_update": ["crm.api.todo.on_update"],
	},
	"Communication": {
		"after_insert": ["crm.utils.on_communication_insert"],
		"on_update": ["crm.utils.on_communication_update"],
	},
	"Comment": {
		"after_insert": ["crm.utils.on_comment_insert"],
		"on_update": ["crm.api.comment.on_update"],
	},
	"WhatsApp Message": {
		"validate": ["crm.api.whatsapp.validate"],
		"on_update": ["crm.api.whatsapp.on_update"],
	},
	"CRM Deal": {
		"after_insert": [
			# E7: catch a Deal created directly as Won (import / quick-create).
			"crm.automation.support_journey.on_deal_update",
		],
		"on_update": [
			"crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.create_customer_in_erpnext",
			# E7: onboarding journey — fires only when the Deal ENTERS a Won status
			# (the handler detects the transition explicitly; not a blind side-effect,
			# and the work is enqueued to a background job).
			"crm.automation.support_journey.on_deal_update",
		],
	},
	# E7: missed-call recovery — seed a callback task for a missed inbound Avaya call.
	"CRM Call Log": {
		"after_insert": ["crm.automation.support_journey.on_call_log_update"],
		"on_update": ["crm.automation.support_journey.on_call_log_update"],
	},
	"Sales Order": {
		"before_validate": [
			"crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.create_customer_on_sales_order"
		],
	},
	"Item": {
		"after_insert": ["crm.integrations.erpnext.item.after_insert"],
		"on_update": ["crm.integrations.erpnext.item.on_update"],
		"before_rename": ["crm.integrations.erpnext.item.before_rename"],
		"after_rename": ["crm.integrations.erpnext.item.after_rename"],
		"on_trash": ["crm.integrations.erpnext.item.on_trash"],
	},
	"User Permission": {
		"before_validate": ["crm.integrations.erpnext.user_permission.before_validate"],
		"after_insert": ["crm.integrations.erpnext.user_permission.after_insert"],
		"on_update": ["crm.integrations.erpnext.user_permission.on_update"],
		"on_trash": ["crm.integrations.erpnext.user_permission.on_trash"],
	},
	"DocShare": {
		"before_validate": ["crm.integrations.erpnext.doc_share.before_validate"],
		"after_insert": ["crm.integrations.erpnext.doc_share.after_insert"],
		"on_update": ["crm.integrations.erpnext.doc_share.on_update"],
		"on_trash": ["crm.integrations.erpnext.doc_share.on_trash"],
	},
	"User": {
		"before_validate": ["crm.api.live_demo.validate_user"],
		"validate_reset_password": ["crm.api.live_demo.validate_reset_password"],
	},
	"Payment Entry": {
		"on_submit": ["crm.finance.payment_hooks.on_payment_entry_submit"],
	},
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"all": ["crm.api.event.trigger_offset_event_notifications"],
	"hourly": ["crm.api.event.trigger_hourly_event_notifications"],
	"daily": [
		"crm.api.event.trigger_daily_event_notifications",
		"crm.fcrm.doctype.crm_view_settings.crm_view_settings.clear_old_versions",
		"crm.telemetry.capture_feature_state",
		"crm.api.quotes.check_quote_expiry",
	],
	"weekly": ["crm.api.event.trigger_weekly_event_notifications"],
	"daily_long": ["crm.lead_syncing.background_sync.sync_leads_from_sources_daily"],
	"hourly_long": ["crm.lead_syncing.background_sync.sync_leads_from_sources_hourly"],
	"monthly_long": ["crm.lead_syncing.background_sync.sync_leads_from_sources_monthly"],
	"cron": {
		"*/5 * * * *": ["crm.lead_syncing.background_sync.sync_leads_from_sources_5_minutes"],
		"*/10 * * * *": ["crm.lead_syncing.background_sync.sync_leads_from_sources_10_minutes"],
		"*/15 * * * *": ["crm.lead_syncing.background_sync.sync_leads_from_sources_15_minutes"],
	},
}

# Testing
# -------

before_tests = "crm.tests.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# "frappe.desk.doctype.event.event.get_events": "crm.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# "Task": "crm.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

ignore_links_on_delete = ["Failed Lead Sync Log"]

# Request Events
# ----------------
# E2-S2: desk fence — block non-allow-listed users from /app|/desk, redirect to the
# branded /access-restricted page. Allow-list = Administrator + site_config
# "desk_access_users". Guests pass through to normal login.
# pin_home_page_to_landing MUST run first: it forces '/' -> index so a System User's
# default_workspace can't resolve the root to /desk/<workspace> and slip past the guard.
before_request = [
	# Re-apply the SES QueueBuilder patch on every web request. The top-level
	# import side-effect above is unreliable: in production (developer_mode off)
	# frappe.get_hooks() serves the hooks dict from the shared redis "app_hooks"
	# cache WITHOUT importing crm.hooks, so a freshly-started web/worker process
	# may never run the module-level patch. apply_queue_builder_patches() is
	# idempotent (guards on a per-class flag), so this is a cheap no-op after the
	# first call. Kept FIRST so guard_desk_access's redirect can't short-circuit it.
	"crm.email.queue_patch.apply_queue_builder_patches",
	"crm.api.route_guard.pin_home_page_to_landing",
	"crm.api.route_guard.guard_desk_access",
]
# after_request = ["crm.utils.after_request"]

# Job Events
# ----------
# Background jobs (enqueued OTP dispatch on the "short" queue, opt-in confirmation
# emails, and the scheduled email-queue flush) run in long-lived RQ workers that
# read hooks from the warm redis cache and never import crm.hooks — so without this
# the SES patch is absent and frappe.sendmail throws OutgoingEmailError at
# queue-build time (nothing is even queued). Idempotent; see before_request note.
before_job = ["crm.email.queue_patch.apply_queue_builder_patches"]
# after_job = ["crm.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# {
# "doctype": "{doctype_1}",
# "filter_by": "{filter_by}",
# "redact_fields": ["{field_1}", "{field_2}"],
# "partial": 1,
# },
# {
# "doctype": "{doctype_2}",
# "filter_by": "{filter_by}",
# "partial": 1,
# },
# {
# "doctype": "{doctype_3}",
# "strict": False,
# },
# {
# "doctype": "{doctype_4}"
# }
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# "crm.auth.validate"
# ]

after_migrate = [
	"crm.fcrm.doctype.fcrm_settings.fcrm_settings.after_migrate",
	"crm.api.whatsapp.add_roles",
	"crm.domain_enrichment.install.seed_default_rules_and_mappings",
	"crm.install.add_default_scripts",
	"crm.install.add_web_form_custom_fields",
	"crm.setup.optin.ensure_signing_key",
	"crm.setup.optin.ensure_default_terms",
	"crm.setup.optin.ensure_lead_source",
]

fixtures = [
	{"dt": "Role", "filters": [["name", "=", "Partner RM"]]},
	{"dt": "Workflow", "filters": [["name", "=", "CRM Lead Approval"]]},
	{"dt": "Print Format", "filters": [["name", "in", ["CRM Quote Standard", "CRM Contract Standard"]]]},
	{"dt": "CRM Product", "filters": [["product_code", "like", "CV-%"]]},
]

standard_dropdown_items = [
	{
		"name1": "app_selector",
		"label": "Apps",
		"type": "Route",
		"route": "#",
		"is_standard": 1,
	},
	{
		"name1": "settings",
		"label": "Settings",
		"type": "Route",
		"icon": "settings",
		"route": "#",
		"is_standard": 1,
	},
	{
		"name1": "login_to_fc",
		"label": "Login to Frappe Cloud",
		"type": "Route",
		"route": "#",
		"is_standard": 1,
	},
	{
		"name1": "about",
		"label": "About",
		"type": "Route",
		"icon": "info",
		"route": "#",
		"is_standard": 1,
	},
	{
		"name1": "separator",
		"label": "",
		"type": "Separator",
		"is_standard": 1,
	},
	{
		"name1": "logout",
		"label": "Log out",
		"type": "Route",
		"icon": "log-out",
		"route": "#",
		"is_standard": 1,
	},
]
