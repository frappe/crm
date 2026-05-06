# crm/integrations/telephony/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

from crm.integrations.telephony.call_linking import CallEvent


@dataclass
class OutboundCallResult:
    """Standardized result from make_outbound_call().

    call_sid may be None for providers that use browser-based calling
    (e.g. Twilio TwiML) where the call_sid arrives via webhook callback
    rather than the initial API response.
    """
    call_sid: str | None
    provider_response: dict


class TelephonyProvider(ABC):
    provider_name: str = ""

    def __init__(self, enabled: bool, settings: dict):
        self.enabled = enabled
        self.settings = settings

    @abstractmethod
    def validate_webhook(self, request_data: dict, require_application_id: bool = False) -> bool:
        """Validate an incoming webhook request. Raise on failure.

        Args:
            request_data: The webhook payload.
            require_application_id: If True, also validate the application/TwiML
                app identifier (used for outbound TwiML endpoints). Providers that
                don't have this concept should ignore the flag.
        """
        ...

    @abstractmethod
    def parse_webhook_to_event(self, request_data: dict) -> CallEvent:
        """Parse raw webhook payload into a standardized CallEvent."""
        ...

    @abstractmethod
    def make_outbound_call(self, from_number: str, to_number: str, caller_user: str) -> OutboundCallResult:
        """Initiate an outbound call. Return an OutboundCallResult.

        call_sid in the result may be None for browser-based calling models
        where the SID arrives asynchronously via webhook.
        """
        ...

    @abstractmethod
    def get_recording_credentials(self) -> tuple[str, str]:
        """Return (api_key, secret) for streaming recordings."""
        ...

    @abstractmethod
    def get_call_status(self, raw_status: str) -> str:
        """Map provider-specific status string to CRM Call Log status."""
        ...

    @abstractmethod
    def is_enabled(self) -> bool:
        """Whether this provider is currently active."""
        ...
