import frappe
from frappe import _
from frappe.auth import LoginManager


@frappe.whitelist(allow_guest=True)
def login():
	if not frappe.conf.demo_username or not frappe.conf.demo_password:
		return
	frappe.local.response["redirect_to"] = "/crm"
	login_manager = LoginManager()
	login_manager.authenticate(frappe.conf.demo_username, frappe.conf.demo_password)
	login_manager.post_login()
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = frappe.local.response["redirect_to"]


def validate_reset_password(user):
	if frappe.conf.demo_username and frappe.session.user == frappe.conf.demo_username:
		frappe.throw(
			_("Password cannot be reset by Demo User {}").format(
				frappe.bold(frappe.conf.demo_username)
			),
			frappe.PermissionError,
		)


def validate_user(doc, event):
	if frappe.conf.demo_username and frappe.session.user == frappe.conf.demo_username and doc.new_password:
		frappe.throw(
			_("Password cannot be reset by Demo User {}").format(
				frappe.bold(frappe.conf.demo_username)
			),
			frappe.PermissionError,
		)

