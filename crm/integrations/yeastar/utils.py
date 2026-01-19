import frappe
from datetime import datetime
from frappe.utils import get_datetime

CTA = "CRM Telephony Agent"


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

    if not frappe.db.exists(CTA, {"user": frappe.session.user, "yeastar": 1}):
        frappe.throw("No Yeaster Telephony Agent found. Please configure one first.")

    caller = frappe.db.get_value(
        CTA, {"user": frappe.session.user, "yeastar": 1}, "yeastar_number"
    )

    return caller


def get_yeastar_agents() -> list[dict[str, str]]:
    return frappe.db.get_all(
        CTA,
        filters={"yeastar": 1},
        fields=["user", "yeastar_number"],
    )


def parse_call_state(payload: dict) -> list[dict] | None:

    try:

        members: list[dict] = payload.get("members", [])
        if not members:
            return None

        yeaster_agents = get_yeastar_agents()
        if not yeaster_agents:
            return None

        agent_lookup = {agent["yeastar_number"]: agent for agent in yeaster_agents}

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

        return results if results else None
    except Exception as e:
        frappe.log_error(
            title="Error parsing call state from Yeastar webhook",
            message=frappe.get_traceback(),
        )
        frappe.throw("Failed to parse call state data.")
        return None
