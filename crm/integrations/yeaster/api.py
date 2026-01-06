import frappe
import requests
from dataclasses import dataclass


@frappe.whitelist(allow_guest=True)
def make_call(caller: str, callee: str, auto_answer: str = "yes") -> None:
    is_yeaster_enabled()

    request_url = url_builder("/call/dial")
    data = {
        "caller": caller,
        "callee": callee,
        "auto_answer": auto_answer,
    }

    make_http_request(
        endpoint=request_url,
        method="POST",
        request_type="make_call",
        data=data,
    )


def make_http_request(
    endpoint: str,
    method: str,
    request_type: str,
    data: dict | None = None,
) -> None:
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
