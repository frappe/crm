from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

import requests
from frappe import _, throw
from frappe.integrations.doctype.integration_request.integration_request import (
	IntegrationRequest,
)
from frappe.integrations.utils import create_request_log

from crm.fcrm.doctype.crm_yeastar_settings.crm_yeastar_settings import (
	CRMYeastarSettings,
)

from .utils import handle_yeastar_error

REQUEST_TIMEOUT_SECONDS = 10


@dataclass
class APIConnector:
	settings_doc: CRMYeastarSettings
	_http_method: str | None = None
	_base_url: str | None = None
	_endpoint: str | None = None
	_headers: dict = field(default_factory=lambda: {"Content-Type": "application/json"})
	_payload: dict = field(default_factory=dict)
	_params: dict | None = None

	def __post_init__(self):
		if not self._base_url:
			self._base_url = self.settings_doc.url

	@property
	def absolute_url(self) -> str:
		if not self.get_urls:
			throw(_("Unrecognized URL configuration"))

		if self._endpoint.startswith(("http://", "https://")):
			return self._endpoint

		return f"{self._base_url.rstrip('/')}/openapi/v1.0/{self._endpoint.lstrip('/')}"

	@property
	def get_urls(self) -> bool:
		return self._base_url and self._endpoint

	@staticmethod
	def get_request_method(method: str) -> Callable[..., requests.Response]:
		methodMap: dict[str, Callable[..., requests.Response]] = {
			"GET": requests.get,
			"POST": requests.post,
		}

		result = methodMap.get(method)

		return result if result else throw(_("Unrecogized HTTP method provided"))

	def set_http_method(self, method: Literal["GET", "POST"]) -> APIConnector:
		self._http_method = method.upper()
		return self

	def set_base_url(self, url: str) -> APIConnector:
		self._base_url = url
		return self

	def set_endpoint(self, endpoint: str) -> APIConnector:
		self._endpoint = endpoint
		return self

	def set_headers(self, headers: dict | None = None) -> APIConnector:
		self._headers = {"Content-Type": "application/json"}
		if headers:
			self._headers.update(headers)
		return self

	def set_params(self, _params: dict) -> APIConnector:
		self._params = _params
		return self

	def set_payload(self, payload: dict | None = None) -> APIConnector:
		self._payload = payload or {}
		return self

	def make_remote_call(self) -> dict:
		int_req_doc: IntegrationRequest = create_request_log(
			data=self._payload or self._params,
			integration_type="Remote",
			service_name="CRM Yeastar Settings",
			request_headers=self._headers,
			url=self.absolute_url,
			is_remote_request=1,
			reference_doctype="CRM Yeastar Settings",
			reference_docname=self.settings_doc.name,
		)

		try:
			response = self.get_request_method(self._http_method)(
				url=self.absolute_url,
				headers=self._headers,
				json=self._payload or None,
				params=self._params,
				timeout=REQUEST_TIMEOUT_SECONDS,
			)

			response.raise_for_status()

		except requests.exceptions.ConnectionError as e:
			self.handle_request_failure(
				int_req_doc,
				self.parse_error(e),
				f"HTTP Request to {self.absolute_url} failed to connect",
			)

		except requests.exceptions.Timeout as e:
			self.handle_request_failure(
				int_req_doc,
				self.parse_error(e),
				f"HTTP Request to {self.absolute_url} timed out after {REQUEST_TIMEOUT_SECONDS} seconds",
			)

		except requests.exceptions.RequestException as e:
			self.handle_request_failure(int_req_doc, self.parse_error(e), f"HTTP Request failed: {e}")

		else:
			data = self.parse_response(response)
			if data.get("errcode") != 0:
				self.handle_request_failure(int_req_doc, data, "An unexpected error occured")
				return {}

			int_req_doc.handle_success(data)

			return data

	@staticmethod
	def parse_response(response: requests.Response) -> dict:
		try:
			return response.json()
		except ValueError:
			return {}

	@staticmethod
	def parse_error(error: Exception) -> dict:
		return {"error": str(error)}

	def handle_request_failure(
		self, integration_req: IntegrationRequest, response: dict, error_message: str
	) -> None:
		integration_req.handle_failure(response)
		handle_yeastar_error(error_message)
