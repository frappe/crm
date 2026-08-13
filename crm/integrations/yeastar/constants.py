from enum import StrEnum

CALL_STATUS_EVENT = "yeastar_call_status_changed"
INCOMING_CALL_EVENT = "yeastar_incoming_call"
INCOMING_CALL_RESOLVED_EVENT = "yeastar_incoming_call_resolved"

INCOMING_CALL_HOLD_SECONDS = 10


class MemberStatus(StrEnum):
	"""`member_status` reported by the PBX for a single leg of a call."""

	ALERT = "ALERT"
	RING = "RING"
	EARLYMEDIA = "EARLYMEDIA"
	ANSWERED = "ANSWERED"
	ANSWER = "ANSWER"
	HOLD = "HOLD"
	BYE = "BYE"


class CallState(StrEnum):
	"""Normalised call state the call popup renders."""

	DIALING = "dialing"
	CONNECTING = "connecting"
	RINGING = "ringing"
	IN_PROGRESS = "in_progress"
	ON_HOLD = "on_hold"
	ENDED = "ended"


class CallDirection(StrEnum):
	INBOUND = "inbound"
	OUTBOUND = "outbound"


class CallAction(StrEnum):
	"""Verdict on a screened inbound call."""

	ACCEPT = "accept"
	REFUSE = "refuse"


ANSWERED_STATUSES = frozenset({MemberStatus.ANSWERED, MemberStatus.ANSWER})

CDR_STATUS_MAP = {
	"ANSWERED": "Completed",
	"BUSY": "Busy",
	"NO ANSWER": "No Answer",
	"NO_ANSWER": "No Answer",
	"NOANSWER": "No Answer",
	"VOICEMAIL": "No Answer",
	"CANCEL": "Canceled",
	"CANCELED": "Canceled",
	"CANCELLED": "Canceled",
	"FAILED": "Failed",
}

STATE_LABELS = {
	CallState.DIALING: "Dialing",
	CallState.CONNECTING: "Connecting",
	CallState.RINGING: "Ringing",
	CallState.IN_PROGRESS: "In call",
	CallState.ON_HOLD: "On hold",
	CallState.ENDED: "Call ended",
}
