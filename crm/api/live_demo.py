# Copyright (c) 2024, Frappe Technologies and contributors
# This file is used to handle live demo site (https://frappecrm-demo.frappe.cloud) related API calls and hooks

import frappe
from frappe import _
from frappe.auth import LoginManager
from frappe.rate_limiter import rate_limit


@frappe.whitelist(allow_guest=True, methods=["GET"])  # nosemgrep: guest-whitelisted-method
@rate_limit(limit=10, seconds=60)
def login():
	if not frappe.conf.demo_username or not frappe.conf.demo_password:
		return
	frappe.local.response["redirect_to"] = "/crm"
	login_manager = LoginManager()
	login_manager.authenticate(frappe.conf.demo_username, frappe.conf.demo_password)
	login_manager.post_login()
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = frappe.local.response["redirect_to"]


def get_demo_user():
	# demo_username is the login email
	return frappe.utils.get_user_by_email(frappe.conf.demo_username)


def validate_reset_password(doc, event):
	if frappe.conf.demo_username and frappe.session.user == get_demo_user():
		frappe.throw(
			_("Password cannot be reset by Demo User {}").format(frappe.bold(frappe.conf.demo_username)),
			frappe.PermissionError,
		)


def validate_user(doc, event):
	if frappe.conf.demo_username and frappe.session.user == get_demo_user() and doc.new_password:
		frappe.throw(
			_("Password cannot be reset by Demo User {}").format(frappe.bold(frappe.conf.demo_username)),
			frappe.PermissionError,
		)
