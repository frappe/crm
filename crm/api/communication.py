import frappe
from frappe.core.doctype.communication.email import make
from frappe.utils import get_formatted_email, parse_addr


@frappe.whitelist()
def send_email(sender: str | None = None, **kwargs):
	sender = _permitted_sender(sender)
	return make(sender=sender, **kwargs)


def _permitted_sender(sender: str | None) -> str:
	user = frappe.session.user
	permitted = {row.email_id for row in frappe.get_cached_doc("User", user).user_emails if row.email_id}
	_, sender_email = parse_addr(sender) if sender else (None, None)
	if sender_email and sender_email in permitted:
		return sender
	return get_formatted_email(user)
