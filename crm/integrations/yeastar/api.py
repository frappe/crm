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
    get_yeaster_agent_by_number,
)
from crm.integrations.exotel.handler import create_call_log
from frappe.model.document import Document
from frappe.utils import get_datetime


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

    response = make_http_request(
        endpoint=request_url,
        method="POST",
        request_type="make_call",
        data=data,
    )

    if create_call_log(
        call_id=response["call_id"],
        from_number=caller,
        to_number=callee,
        medium=callee,
        status="Ringing",
        call_type="Outgoing",
        telephony_medium="Yeastar",
        agent=frappe.session.user,
    ):

        return response


@dataclass
class IncomingCallDetails:
    caller: str
    callee: str
    channel_id: str
    call_id: str


@frappe.whitelist(allow_guest=True)
def handle_incoming_call() -> None:
    data: dict[str, str] = frappe.request.get_json()

    if not data:
        frappe.log_error(
            "No data received in the incoming call webhook.",
            "Yeastar Incoming Call Webhook Error",
        )
        frappe.throw("No data received from the incoming call webhook.")

    call_id = data.get("call_id")
    members: list[dict] = data.get("members")
    inbound_info_data: dict = members[0].get("inbound")

    caller = inbound_info_data.get("from")
    callee = inbound_info_data.get("to")
    channel_id = inbound_info_data.get("channel_id")

    details = IncomingCallDetails(
        caller=caller, callee=callee, channel_id=channel_id, call_id=call_id
    )

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
    direction: str


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
        return

    for entry in data_parsed:
        details = CallStatusDetails(
            user=entry["user"],
            status=entry["status"],
            client_number=entry["client_number"],
            channel_id=entry["channel_id"],
            call_id=entry["call_id"],
            direction=entry["direction"],
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

    if isinstance(details, IncomingCallDetails):
        create_call_log(
            call_id=details.call_id,
            from_number=details.caller,
            to_number=details.callee,
            medium=details.callee,
            status="Ringing",
            call_type="Incoming",
            telephony_medium="Yeastar",
            agent=get_yeaster_agent_by_number(details.caller),
        )


@frappe.whitelist(allow_guest=True)
def update_call_log():

    try:

        frappe.set_user("Yeastar Call Log Webhook")

        data: dict[str, str] = frappe.request.get_json()
        if not data:
            frappe.log_error(
                "No data received in the update call log webhook.",
                "Yeastar Update Call Log Webhook Error",
            )
            return
        frappe.log_error(
            title="Call Log Webhook Data",
            message=str(data),
        )

        if call_log_doc := get_call_log(data["call_id"]):
            call_log_doc.status = map_call_log_status(data["status"])
            call_log_doc.duration = data["talk_duration"]
            call_log_doc.start_time = data["time_start"]
            call_log_doc.end_time = get_datetime()

            call_log_doc.save(ignore_permissions=True)
            frappe.db.commit()

            frappe.log_error(
                title="Call Log Updated",
                message=f"Call Log {call_log_doc.as_dict()} updated.",
            )

    except Exception:
        frappe.log_error(
            title="Error while updating call log from Yeastar webhook",
            message=frappe.get_traceback(),
        )

    finally:
        frappe.set_user("Guest")


def map_call_log_status(status: str) -> str:

    status_map = {
        "ANSWERED": "Completed",
        "BUSY": "Busy",
        "NO ANSWER": "No Answer",
    }

    return status_map[status] if status in status_map else "Failed"


def get_call_log(call_log_id: str) -> "Document":
    if frappe.db.exists("CRM Call Log", call_log_id):
        return frappe.get_doc("CRM Call Log", call_log_id)


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
