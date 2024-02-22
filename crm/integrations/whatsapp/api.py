import json
import frappe
from werkzeug.wrappers import Response

from frappe.integrations.utils import make_post_request

def whatsapp_settings():
    """Get whatsapp settings."""
    return frappe.get_cached_doc("CRM Whatsapp Settings")


@frappe.whitelist(allow_guest=True)
def webhook():
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
    data = frappe.local.form_dict
    try:
        frappe.get_doc(
            {"doctype": "CRM Whatsapp Log", "data": json.dumps(data, indent=2)}
        ).insert(ignore_permissions=True)

        messages = data["entry"][0]["changes"][0]["value"].get("messages", [])

        if messages:
            for message in messages:
                message_type = message["type"]
                if message_type == "text":
                    frappe.get_doc(
                        {
                            "doctype": "CRM Whatsapp Message",
                            "from": message["from"],
                            "direction": "Incoming",
                            "message_id": message["id"],
                            "message_type": message_type,
                            "message": message["text"]["body"],
                            "data": json.dumps(message, indent=2),
                        }
                    ).insert(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(e)
        return Response("Error", status=500)


@frappe.whitelist()
def send_message(data, to):
    whatsapp_settings = frappe.get_cached_doc("CRM Whatsapp Settings")
    url = whatsapp_settings.url
    token = whatsapp_settings.get_password("token")
    phone_no_id = whatsapp_settings.phone_no_id
    version = whatsapp_settings.version

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": "hello_world",
            "language": {"code": "en_US"},
        },
    }
    message = data["template"]
    type = "Template"
    message_type = "template"
    # data = {
    #     "messaging_product": "whatsapp",
    #     "to": to,
    #     "text": {
    #         "body": "New World",
    #     },
    # }
    # message = data["text"]["body"]
    # type = "Manual"
    # message_type = "text"
    headers = {"authorization": f"Bearer {token}", "content-type": "application/json"}

    try:
        response = make_post_request(
            f"{url}/{version}/{phone_no_id}/messages",
            headers=headers,
            data=json.dumps(data),
        )
        frappe.get_doc(
            {
                "doctype": "CRM Whatsapp Message",
                "direction": "Outgoing",
                "message": str(message),
                "type": type,
                "to": to,
                "message_id": response["messages"][0]["id"],
                "message_type": message_type,
                "data": json.dumps(response, indent=2),
            }
        ).save(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(e)
        return None
