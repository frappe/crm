import frappe
import requests
from dataclasses import dataclass
from typing import Literal
from .utils import (
    is_yeaster_enabled,
    url_builder,
    validate_token,
    get_yeaster_number,
    parse_call_state,
)


@frappe.whitelist(allow_guest=True)
def make_call(callee: str, auto_answer: str = "yes") -> dict[str, str]:
    is_yeaster_enabled()

    validate_token()

    request_url = url_builder("/call/dial")

    caller = get_yeaster_number()
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


@dataclass
class IncomingCallDetails:
    caller: str
    callee: str
    channel_id: str


@frappe.whitelist(allow_guest=True)
def handle_incoming_call() -> None:
    data: dict[str, str] = frappe.request.get_json()

    if not data:
        frappe.log_error(
            "No data received in the incoming call webhook.",
            "Yeastar Incoming Call Webhook Error",
        )
        frappe.throw("No data received from the incoming call webhook.")

    members: list[dict] = data.get("members")
    inbound_info_data: dict = members[0].get("inbound")

    caller = inbound_info_data.get("from")
    callee = inbound_info_data.get("to")
    channel_id = inbound_info_data.get("channel_id")

    details = IncomingCallDetails(caller=caller, callee=callee, channel_id=channel_id)

    create_socket_connection(details)


@frappe.whitelist(allow_guest=True)
def respond_to_call(channel_id: str, action: Literal["accept", "refuse"]) -> dict:

    validate_token()

    request_url = url_builder(f"/call/{action}_inbound")
    data = {"channel_id": channel_id}
    return make_http_request(
        endpoint=request_url,
        method="POST",
        request_type=f"{action}_call",
        data=data,
    )


@frappe.whitelist(allow_guest=True)
def hangup_call(channel_id: str) -> dict:

    validate_token()

    request_url = url_builder("/call/hangup")
    data = {"channel_id": channel_id}
    return make_http_request(
        endpoint=request_url,
        method="POST",
        request_type="hangup_call",
        data=data,
    )


@dataclass
class CallStatusDetails:
    user: str
    status: str
    client_number: str
    channel_id: str
    call_id: str


@frappe.whitelist(allow_guest=True)
def call_status_changed():
    data: dict = frappe.request.get_json()
    if not data:
        frappe.log_error(
            "No data received in the call status changed webhook.",
            "Yeastar Call Status Changed Webhook Error",
        )

    data_parsed = parse_call_state(data)
    if not data_parsed:
        frappe.log_error(
            title="Yeastar Call Status Changed Webhook - My Extension Not Present",
            message="The call does not involve the configured Yeastar extension.",
        )
        return

    for entry in data_parsed:
        details = CallStatusDetails(
            user=entry["user"],
            status=entry["status"],
            client_number=entry["client_number"],
            channel_id=entry["channel_id"],
            call_id=entry["call_id"],
        )

        create_socket_connection(details)


def create_socket_connection(details: IncomingCallDetails | CallStatusDetails) -> None:

    if isinstance(details, IncomingCallDetails):
        event_name = "yeastar_incoming_call"
    else:
        event_name = "yeastar_call_status_changed"

    frappe.publish_realtime(
        event=event_name,
        message=details.__dict__,
        user=details.user if hasattr(details, "user") else None,
    )


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
            title=f"Error while making request of type {request_type.upper()} to Yeastar API: {str(e)}",
            message=frappe.get_traceback(),
        )
        frappe.throw("There was an error connecting to the Yeastar API.")


@frappe.whitelist()
def create_call_log_entry(call_details: dict):

    try:

        _from = (
            frappe.session.user
            if call_details["from"] == "session_user"
            else call_details["from"]
        )
        _to = (
            frappe.session.user
            if call_details["to"] == "session_user"
            else call_details["to"]
        )

        if call_details["to"] == "session_user":
            _to = frappe.session.user

        crm_call_log_doc = frappe.get_doc(
            {
                "doctype": "CRM Call Log",
                "telephony_medium": call_details["telephony_medium"],
                "status": call_details["status"],
                "type": call_details["type"],
                "from": _from,
                "to": _to,
                "duration": call_details["duration"],
            }
        )

        crm_call_log_doc.insert(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title=f"Error creating call log entry: {str(e)}",
        )
