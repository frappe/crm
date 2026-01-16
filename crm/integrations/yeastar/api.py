import frappe
import requests
from dataclasses import dataclass
from typing import Literal
from .utils import (
    is_yeaster_enabled,
    url_builder,
    validate_token,
    get_yeaster_number,
    get_yeastar_agents,
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


@frappe.whitelist(allow_guest=True)
def call_status_changed():
    data: dict = frappe.request.get_json()
    if not data:
        frappe.log_error(
            "No data received in the call status changed webhook.",
            "Yeastar Call Status Changed Webhook Error",
        )

    frappe.log_error(
        title="Yeastar Call Status Changed Webhook Data",
        message=str(data),
    )
    data_parsed = parse_call_state(data)
    if not data_parsed:
        frappe.log_error(
            title="Yeastar Call Status Changed Webhook - My Extension Not Present",
            message="The call does not involve the configured Yeastar extension.",
        )
        return

    frappe.log_error(
        title="Yeastar Call Status Changed Webhook Data",
        message=data_parsed,
    )

    for entry in data_parsed:
        details = CallStatusDetails(
            user=entry["user"],
            status=entry["status"],
            client_number=entry["client_number"],
            channel_id=entry["channel_id"],
        )

        create_socket_connection(details)


def parse_call_state(payload: dict) -> list[dict] | None:
    frappe.log_error(
        title="Yeastar Call Status Changed Webhook - Payload Received",
        message=str(payload),
    )
    try:

        members: list[dict] = payload.get("members", [])
        if not members:
            return None

        yeaster_agents = get_yeastar_agents()
        if not yeaster_agents:
            return None

        agent_lookup = {agent["yeastar_number"]: agent for agent in yeaster_agents}
        frappe.log_error(
            title="Yeastar Call Status Changed Webhook - Agent Lookup",
            message=str(agent_lookup),
        )

        results = []

        for member in members:
            if "extension" in member:
                ext_data = member["extension"]
                ext_number = ext_data.get("number")
                channel_id = ext_data.get("channel_id")

                if ext_number in agent_lookup:
                    agent = agent_lookup[ext_number]

                    external_party = None
                    direction = None

                    for m in members:
                        if "inbound" in m:
                            external_party = m["inbound"]
                            direction = "inbound"
                            break
                        elif "outbound" in m:
                            external_party = m["outbound"]
                            direction = "outbound"
                            break

                    if external_party and direction:
                        client_number = (
                            external_party.get("from")
                            if direction == "inbound"
                            else external_party.get("to")
                        )

                        client_status = external_party.get("member_status")

                        results.append(
                            {
                                "user": agent["user"],
                                "status": client_status,
                                "client_number": client_number,
                                "channel_id": channel_id,
                            }
                        )
        frappe.log_error(
            title="Yeastar Call Status Changed Webhook - Parsed Results",
            message=str(results),
        )

        return results if results else None
    except Exception as e:
        frappe.log_error(
            title="Error parsing call state from Yeastar webhook",
            message=frappe.get_traceback(),
        )
        return None


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
