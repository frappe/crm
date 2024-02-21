import frappe
from werkzeug.wrappers import Response

def whatsapp_settings():
    """Get whatsapp settings."""
    return frappe.get_cached_doc("CRM Whatsapp Settings")

@frappe.whitelist(allow_guest=True)
def verify_webhook():
    """Meta webhook."""
    if frappe.request.method == "GET":
        return get()
    return post()

def get():
    """Get."""
    challenge = frappe.form_dict.get("hub.challenge")
    webhook_token = whatsapp_settings().webhook_token

    if frappe.form_dict.get("hub.verify_token") != webhook_token:
        frappe.throw("Verify token does not match")

    return Response(challenge, status=200)

def post():
    """Post."""
    pass