import frappe
from datetime import datetime
from frappe.utils import get_datetime


def yeaster_settings():
    return frappe.get_doc("CRM Yeastar Settings")


def is_yeaster_enabled() -> None:
    if not (yeaster_settings()):
        frappe.throw(
            "Yeastar integration is not enabled. Please configure the settings first."
        )


def url_builder(path: str) -> str:
    settings = yeaster_settings()
    return f"{settings.request_url}{path}?access_token={settings.access_token}"


def validate_token() -> None:
    settings = yeaster_settings()

    expiry_date = get_datetime(settings.access_token_expiry)
    now = datetime.now()

    if expiry_date < now:
        settings.save(ignore_permissions=True)


def get_yeaster_number() -> str:
    CTA = "CRM Telephony Agent"
    if not frappe.db.exists(CTA, {"user": frappe.session.user, "yeastar": 1}):
        frappe.throw("No Yeaster Telephony Agent found. Please configure one first.")

    caller = frappe.db.get_value(
        CTA, {"user": frappe.session.user, "yeastar": 1}, "yeastar_number"
    )

    return caller


