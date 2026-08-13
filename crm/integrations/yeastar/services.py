from dataclasses import asdict, dataclass, field

import frappe
from frappe import _
from frappe.utils import add_to_date, cint, get_datetime

from crm.integrations.exotel.handler import create_call_log

from .api_connector import APIConnector
from .constants import (
	ANSWERED_STATUSES,
	CALL_STATUS_EVENT,
	CDR_STATUS_MAP,
	INCOMING_CALL_EVENT,
	INCOMING_CALL_HOLD_SECONDS,
	INCOMING_CALL_RESOLVED_EVENT,
	STATE_LABELS,
	CallAction,
	CallDirection,
	CallState,
	MemberStatus,
)
from .utils import (
	get_call_log,
	get_yeastar_agents,
	get_yeaster_number,
	is_yeaster_enabled,
	validate_session_user,
)


@dataclass
class TokenService(APIConnector):
	def __post_init__(self):
		super().__post_init__()

	def issue_token(self) -> str:
		token_response = (
			self.set_http_method("POST")
			.set_endpoint("get_token")
			.set_payload(
				{
					"username": self.settings_doc.username,
					"password": self.settings_doc.get_password(),
				}
			)
			.make_remote_call()
		)
		self.update_settings(token_response)

		return token_response.get("access_token")

	def refresh_token(self) -> None:
		token_response = (
			self.set_http_method("POST")
			.set_endpoint("refresh_token")
			.set_payload(
				{
					"refresh_token": self.settings_doc.refresh_token,
				}
			)
			.make_remote_call()
		)
		self.update_settings(token_response)

	def update_settings(self, response: dict | None) -> None:
		if not response:
			return

		access_token_expire_time = response.get("access_token_expire_time")
		refresh_token_expire_time = response.get("refresh_token_expire_time")
		current_datetime = get_datetime()

		data = {
			"access_token": response.get("access_token"),
			"access_token_expire_duration": response.get("access_token_expire_time"),
			"refresh_token": response.get("refresh_token"),
			"refresh_token_expire_duration": response.get("refresh_token_expire_time"),
			"access_token_issue": current_datetime,
			"access_token_expiry": add_to_date(current_datetime, seconds=access_token_expire_time),
			"refresh_token_issue": current_datetime,
			"refresh_token_expiry": add_to_date(current_datetime, seconds=refresh_token_expire_time),
		}
		self.settings_doc.db_set(data, update_modified=False)
		self.settings_doc.reload()


@dataclass
class CallService(APIConnector):
	def __post_init__(self):
		super().__post_init__()

	def validate_agent(self) -> None:
		if not validate_session_user():
			frappe.throw(_("Logged In User is not a telephony agent"), frappe.PermissionError)

		is_yeaster_enabled()

	def call_control(self, endpoint: str, channel_id: str) -> dict:
		"""Issue a call-control command against a single leg of a live call."""
		return (
			self.set_http_method("POST")
			.set_endpoint(endpoint)
			.set_params({"access_token": self.settings_doc.generate_access_token()})
			.set_payload({"channel_id": channel_id})
			.make_remote_call()
		)

	def trigger_call(self, callee: str) -> dict[str, str]:
		self.validate_agent()

		caller = get_yeaster_number()
		data = {
			"caller": caller,
			"callee": callee,
			"auto_answer": "yes",
		}

		response = (
			self.set_http_method("POST")
			.set_endpoint("call/dial")
			.set_params({"access_token": self.settings_doc.generate_access_token()})
			.set_payload(data)
			.make_remote_call()
		)

		if call_id := response.get("call_id"):
			create_call_log(
				call_id=call_id,
				from_number=caller,
				to_number=callee,
				medium=callee,
				status="Ringing",
				call_type="Outgoing",
				telephony_medium="Yeastar",
				agent=frappe.session.user,
			)

		return response

	def respond_to_call(self, channel_id: str, action: str) -> dict:
		"""Accept or refuse a screened inbound call still held at the trunk."""
		self.validate_agent()

		try:
			verdict = CallAction(action)
		except ValueError:
			frappe.throw(_("Unrecognised call action: {0}").format(action))

		response = self.call_control(f"call/{verdict}_inbound", channel_id)

		self.publish_to_agents(
			INCOMING_CALL_RESOLVED_EVENT,
			{
				"channel_id": channel_id,
				"action": str(verdict),
				"resolved_by": frappe.session.user,
			},
		)

		return response

	def hangup(self, channel_id: str) -> dict:
		self.validate_agent()

		return self.call_control("call/hangup", channel_id)

	def handle_incoming_call(self, payload: dict | None) -> None:
		"""Fan a Yeastar `Incoming Call Request` out to the telephony team."""
		try:
			event = self.parse_incoming_call(payload)
			if not event:
				return

			self.publish_to_agents(INCOMING_CALL_EVENT, asdict(event))

			if get_call_log(event.call_id):
				return

			create_call_log(
				call_id=event.call_id,
				from_number=event.caller,
				to_number=event.callee,
				medium=event.callee,
				status="Ringing",
				call_type="Incoming",
				telephony_medium="Yeastar",
				agent=None,
			)
		except Exception:
			frappe.log_error(
				title="Yeastar: failed to handle incoming call event",
				message=frappe.get_traceback(),
			)

	def parse_incoming_call(self, payload: dict | None) -> "IncomingCallEvent | None":
		if not payload:
			return None

		call_id = payload.get("call_id")
		leg, _direction = self.find_external_leg(payload.get("members") or [])
		if not call_id or not leg:
			return None

		return IncomingCallEvent(
			call_id=call_id,
			caller=leg.get("from"),
			callee=leg.get("to"),
			channel_id=leg.get("channel_id"),
			trunk_name=leg.get("trunk_name"),
			hold_seconds=INCOMING_CALL_HOLD_SECONDS,
		)

	def update_call_log(self, payload: dict | None) -> None:
		"""Finalise a call log from a Yeastar `Call End` (CDR) event."""
		try:
			if not payload or not (call_id := payload.get("call_id")):
				return

			call_log = get_call_log(call_id)
			if not call_log:
				return

			talk_duration = cint(payload.get("talk_duration"))
			start_time = get_datetime(payload.get("time_start")) or call_log.start_time

			call_log.status = CDR_STATUS_MAP.get((payload.get("status") or "").upper(), "Failed")
			call_log.duration = talk_duration
			call_log.start_time = start_time
			call_log.end_time = add_to_date(
				start_time, seconds=cint(payload.get("call_duration")) or talk_duration
			)

			call_log.save(ignore_permissions=True)
			frappe.db.commit()
		except Exception:
			frappe.log_error(
				title="Yeastar: failed to finalise call log",
				message=frappe.get_traceback(),
			)

	@staticmethod
	def publish_to_agents(event: str, message: dict) -> None:
		for agent in get_yeastar_agents():
			frappe.publish_realtime(event=event, message=message, user=agent["user"])

	def call_status_changed(self, payload: dict | None) -> None:
		"""Fan a Yeastar `Call Status Changed` event out to the agents it concerns."""
		try:
			for event in self.parse_call_events(payload):
				frappe.publish_realtime(
					event=CALL_STATUS_EVENT,
					message=asdict(event),
					user=event.user,
				)
		except Exception:
			frappe.log_error(
				title="Yeastar: failed to handle call status event",
				message=frappe.get_traceback(),
			)

	def parse_call_events(self, payload: dict | None) -> list["CallStateEvent"]:
		"""Turn one webhook body into one event per agent extension it names."""
		if not payload:
			return []

		call_id = payload.get("call_id")
		members: list[dict] = payload.get("members") or []
		if not call_id or not members:
			return []

		agents = {agent["yeastar_number"]: agent["user"] for agent in get_yeastar_agents()}
		if not agents:
			return []

		external, direction = self.find_external_leg(members)
		external_status = (external or {}).get("member_status")

		events = []
		for member in members:
			extension = member.get("extension")
			if not extension:
				continue

			user = agents.get(extension.get("number"))
			if not user:
				continue

			state = self.resolve_state(extension.get("member_status"), external_status, direction)

			events.append(
				CallStateEvent(
					call_id=call_id,
					user=user,
					agent_number=extension.get("number"),
					direction=direction,
					state=state,
					label=STATE_LABELS[state],
					extension_status=extension.get("member_status"),
					external_status=external_status,
					client_number=self.get_client_number(external, direction),
					extension_channel_id=extension.get("channel_id"),
					external_channel_id=(external or {}).get("channel_id"),
					is_final=state == CallState.ENDED,
				)
			)

		return events

	@staticmethod
	def find_external_leg(members: list[dict]) -> tuple[dict | None, str | None]:
		"""Locate the leg facing the outside world, and the call's direction."""
		for member in members:
			for direction in (CallDirection.INBOUND, CallDirection.OUTBOUND):
				if leg := member.get(direction):
					return leg, direction

		return None, None

	@staticmethod
	def get_client_number(external: dict | None, direction: str | None) -> str | None:
		if not external:
			return None

		return external.get("from") if direction == CallDirection.INBOUND else external.get("to")

	@staticmethod
	def resolve_state(
		extension_status: str | None,
		external_status: str | None,
		direction: str | None,
	) -> CallState:
		"""Collapse two leg statuses into the one state the popup renders."""
		if MemberStatus.BYE in (extension_status, external_status):
			return CallState.ENDED

		driver = extension_status if direction == CallDirection.INBOUND else external_status

		if driver is None:
			return CallState.CONNECTING if extension_status in ANSWERED_STATUSES else CallState.DIALING

		if driver in ANSWERED_STATUSES:
			return CallState.IN_PROGRESS

		if driver == MemberStatus.HOLD:
			return CallState.ON_HOLD

		return CallState.RINGING


@dataclass(frozen=True)
class IncomingCallEvent:
	"""A call held at the trunk, awaiting a screening verdict."""

	call_id: str
	caller: str | None
	callee: str | None
	channel_id: str | None
	trunk_name: str | None
	hold_seconds: int


@dataclass(frozen=True)
class CallStateEvent:
	"""One agent's view of a call, as published to their browser."""

	call_id: str
	user: str
	agent_number: str
	direction: str | None
	state: str
	label: str
	extension_status: str | None
	external_status: str | None
	client_number: str | None
	extension_channel_id: str | None
	external_channel_id: str | None
	is_final: bool
	hangup_channel_id: str | None = field(default=None)

	def __post_init__(self):
		object.__setattr__(
			self,
			"hangup_channel_id",
			self.extension_channel_id or self.external_channel_id,
		)
