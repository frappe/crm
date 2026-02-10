# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests
import json
from frappe.utils import getdate
from datetime import datetime, timedelta


class CRMYeastarSettings(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        access_token: DF.Data | None
        access_token_expire_duration: DF.Int
        access_token_expiry: DF.Datetime | None
        enabled: DF.Check
        password: DF.Data | None
        refresh_token: DF.Data | None
        refresh_token_expire_duration: DF.Int
        request_url: DF.Data | None
        username: DF.Data | None
    # end: auto-generated types
    pass

    def validate(self):
        if self.enabled:
            if self.generate_access_token():
                frappe.msgprint("Access token generated successfully.")

    def generate_access_token(self) -> bool:

        request_url: str = self.request_url + "/get_token"

        payload = {
            "username": self.username,
            "password": self.password,
        }

        response = self.make_http_request(
            endpoint=request_url,
            request_type="GENERATE_TOKEN",
            data=payload,
        )
        self.access_token = response.get("access_token")
        self.refresh_token = response.get("refresh_token")
        self.access_token_expiry = datetime.now() + timedelta(
            seconds=response.get("access_token_expire_time")
        )
        self.refresh_token_expire_duration = response.get("refresh_token_expire_time")
        self.access_token_expire_duration = response.get("access_token_expire_time")

    def make_http_request(self, endpoint: str, request_type: str, data: dict) -> dict:
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url=endpoint, json=data, headers=headers)

            response.raise_for_status()
            response_data = response.json()

            if response_data.get("errcode") != 0:
                frappe.throw(
                    f"{response_data.get('errmsg', 'Unknown error')}. ERROR CODE: {response_data.get('errcode')}"
                )

            return response_data

        except Exception as e:
            frappe.log_error(
                title=f"Error while making request of type {request_type} to Yeastar API: {str(e)}",
                message=frappe.get_traceback(),
            )
            frappe.throw("There was an error connecting to the Yeastar API.")

    def refresh_access_token(self):
        request_url: str = self.request_url + "/refresh_token"

        payload = {
            "refresh_token": self.refresh_token,
        }

        response = self.make_http_request(
            endpoint=request_url,
            request_type="REFRESH_TOKEN",
            data=payload,
        )

        self.access_token = response.get("access_token")
        self.refresh_token = response.get("refresh_token")
        self.access_token_expiry = datetime.now() + timedelta(
            seconds=response.get("access_token_expire_time")
        )
