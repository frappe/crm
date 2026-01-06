import frappe
import requests
from dataclasses import dataclass


@frappe.whitelist(allow_guest=True)
def make_call(caller: str, callee: str, auto_answer: str = "yes") -> dict[str, str]:
    is_yeaster_enabled()

    request_url = url_builder("/call/dial")
    data = {
        "caller": caller,
        "callee": callee,
        "auto_answer": auto_answer,
    }

    return make_http_request(
        endpoint=request_url,
        method="POST",
        request_type="make_call",
        data=data,
    )


@frappe.whitelist(allow_guest=True)
def handle_incoming_call() -> None:
    data: dict[str, str] = frappe.request.get_json()
    if not data:
        frappe.log_error(
            "No data received in the incoming call webhook.",
            "Yeastar Incoming Call Webhook Error",
        )
        frappe.throw("No data received from the incoming call webhook.")

    members: list[dict] = data.get("msg").get("members")
    inbound_info_data: dict = members[0].get("inbound")

    caller = inbound_info_data.get("from")
    callee = inbound_info_data.get("to")
    channel_id = inbound_info_data.get("channel_id")

    details = IncomingCallDetails(caller=caller, callee=callee, channel_id=channel_id)

    create_socket_connection(details)


@dataclass
class IncomingCallDetails:
    caller: str
    callee: str
    channel_id: str


def create_socket_connection(details: IncomingCallDetails) -> None:

    frappe.publish_realtime(
        event="yeastar_incoming_call",
        message=details.__dict__,
        user=frappe.session.user,
    )


@frappe.whitelist(allow_guest=True)
def accept_call():
    pass


def make_http_request(
    endpoint: str,
    method: str,
    request_type: str,
    data: dict | None = None,
) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}

    try:
        if method.upper() == "POST":
            response = requests.post(url=endpoint, json=data, headers=headers)
        elif method.upper() == "GET":
            response = requests.get(url=endpoint, headers=headers)

        response.raise_for_status()
        response_data = response.json()

        if response_data.get("errcode") != 0:
            frappe.throw(
                f"{response_data.get('errmsg', 'Unknown error')}. ERROR CODE: {response_data.get('errcode')}"
            )

        return response_data

    except Exception as e:
        frappe.log_error(
            f"Error while making request of type {request_type.upper()} to Yeastar API: {str(e)}",
            "Yeastar API Request Error",
        )
        frappe.throw("There was an error connecting to the Yeastar API.")


def url_builder(path: str) -> str:
    settings = yeaster_settings()
    return f"{settings.request_url}{path}?access_token={settings.access_token}"


def is_yeaster_enabled() -> None:
    if not (yeaster_settings()):
        frappe.throw(
            "Yeastar integration is not enabled. Please configure the settings first."
        )


def yeaster_settings():
    return frappe.get_doc("CRM Yeastar Settings")
