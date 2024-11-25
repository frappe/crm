import frappe
from bs4 import BeautifulSoup
from frappe.core.api.file import get_max_file_size
from frappe.translate import get_all_translations
from frappe.utils import cstr
from frappe.utils.telemetry import POSTHOG_HOST_FIELD, POSTHOG_PROJECT_FIELD


@frappe.whitelist(allow_guest=True)
def get_translations():
    if frappe.session.user != "Guest":
        language = frappe.db.get_value("User", frappe.session.user, "language")
    else:
        language = frappe.db.get_single_value("System Settings", "language")

    return get_all_translations(language)


@frappe.whitelist()
def get_user_signature():
    user = frappe.session.user
    user_email_signature = (
        frappe.db.get_value(
            "User",
            user,
            "email_signature",
        )
        if user
        else None
    )

    signature = user_email_signature or frappe.db.get_value(
        "Email Account",
        {"default_outgoing": 1, "add_signature": 1},
        "signature",
    )

    if not signature:
        return

    soup = BeautifulSoup(signature, "html.parser")
    html_signature = soup.find("div", {"class": "ql-editor read-mode"})
    _signature = None
    if html_signature:
        _signature = html_signature.renderContents()
    content = ""
    if cstr(_signature) or signature:
        content = f'<br><p class="signature">{signature}</p>'
    return content


@frappe.whitelist()
def get_posthog_settings():
    return {
        "posthog_project_id": frappe.conf.get(POSTHOG_PROJECT_FIELD),
        "posthog_host": frappe.conf.get(POSTHOG_HOST_FIELD),
        "enable_telemetry": frappe.get_system_settings("enable_telemetry"),
        "telemetry_site_age": frappe.utils.telemetry.site_age(),
    }


def check_app_permission():
    if frappe.session.user == "Administrator":
        return True

    roles = frappe.get_roles()
    if any(
        role
        in ["System Manager", "Sales User", "Sales Manager", "Sales Master Manager"]
        for role in roles
    ):
        return True

    return False


@frappe.whitelist()
def get_file_uploader_defaults(doctype: str):
    max_number_of_files = None
    make_attachments_public = False
    if doctype:
        meta = frappe.get_meta(doctype)
        max_number_of_files = meta.get("max_attachments")
        make_attachments_public = meta.get("make_attachments_public")

    return {
        "allowed_file_types": frappe.get_system_settings("allowed_file_extensions"),
        "max_file_size": get_max_file_size(),
        "max_number_of_files": max_number_of_files,
        "make_attachments_public": bool(make_attachments_public),
    }
