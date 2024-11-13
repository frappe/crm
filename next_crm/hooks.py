app_name = "next_crm"
app_title = "Next CRM"
app_publisher = "rtCamp"
app_description = "Kick-ass Open Source CRM"
app_email = "erp@rtcamp.com"
app_license = "GNU AFFERO GENERAL PUBLIC LICENSE (v3)"
app_icon_url = "/assets/next_crm/images/logo.svg"
app_icon_title = "Next CRM"
app_icon_route = "/next-crm"

# Apps
# ------------------

# required_apps = []
add_to_apps_screen = [
	{
		"name": "next_crm",
		"logo": "/assets/next_crm/images/logo.svg",
		"title": "Next CRM",
		"route": "/next-crm",
		"has_permission": "next_crm.api.check_app_permission",
	}
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assetsnext_crm/css/next_crm.css"
# app_include_js = "/assetsnext_crm/js/next_crm.js"

# include js, css files in header of web template
# web_include_css = "/assetsnext_crm/css/next_crm.css"
# web_include_js = "/assetsnext_crm/js/next_crm.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = next_crm/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Lead": "public/js/lead.js",
    "Opportunity": "public/js/opportunity.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

website_route_rules = [
	{"from_route": "/next-crm/<path:app_path>", "to_route": "next-crm"},
]

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "next_crm.utils.jinja_methods",
#	"filters": "next_crm.utils.jinja_filters"
# }

# Installation
# ------------

before_install = "next_crm.install.before_install"
after_install = "next_crm.install.after_install"

# Uninstallation
# ------------

before_uninstall = "next_crm.uninstall.before_uninstall"
# after_uninstall = "next_crm.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "next_crm.utils.before_app_install"
# after_app_install = "next_crm.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "next_crm.utils.before_app_uninstall"
# after_app_uninstall = "next_crm.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "next_crm.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Contact": "next_crm.overrides.contact.CustomContact",
	"Email Template": "next_crm.overrides.email_template.CustomEmailTemplate",
	"User": "next_crm.overrides.user.CustomUser",
	"Customer": "next_crm.overrides.customer.Customer",
	"Lead": "next_crm.overrides.lead.Lead",
	"Customize Form": "next_crm.overrides.customize_form.CustomizeFormOverride",
    "Opportunity": "next_crm.overrides.opportunity.Opportunity",
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Contact": {
		"validate": ["next_crm.api.contact.validate"],
	},
	"ToDo": {
		"after_insert": ["next_crm.api.todo.after_insert"],
		"on_update": ["next_crm.api.todo.on_update"],
	},
	"Comment": {
		"on_update": ["next_crm.api.comment.on_update"],
	},
	"WhatsApp Message": {
		"validate": ["next_crm.api.whatsapp.validate"],
		"on_update": ["next_crm.api.whatsapp.on_update"],
	},
	"User": {
		"before_validate": ["next_crm.api.demo.validate_user"],
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"next_crm.tasks.all"
#	],
#	"daily": [
#		"next_crm.tasks.daily"
#	],
#	"hourly": [
#		"next_crm.tasks.hourly"
#	],
#	"weekly": [
#		"next_crm.tasks.weekly"
#	],
#	"monthly": [
#		"next_crm.tasks.monthly"
#	],
# }

# Testing
# -------

# before_tests = "next_crm.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "next_crm.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "next_crm.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["next_crm.utils.before_request"]
# after_request = ["next_crm.utils.after_request"]

# Job Events
# ----------
# before_job = ["next_crm.utils.before_job"]
# after_job = ["next_crm.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"next_crm.auth.validate"
# ]

fixtures = [
	{
		"dt": "Property Setter",
		"filters": [
			[
				"module",
				"in",
				["NCRM"],
			]
		],
	},
	{
		"dt": "Custom Field",
		"filters": [
			[
				"module",
				"in",
				["NCRM"],
			]
		],
	},
]
