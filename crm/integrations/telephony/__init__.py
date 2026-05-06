from crm.integrations.telephony.base import OutboundCallResult, TelephonyProvider
from crm.integrations.telephony.call_linking import CallEvent, link_call_log_to_record
from crm.integrations.telephony.registry import TelephonyRegistry

__all__ = ["OutboundCallResult", "TelephonyProvider", "CallEvent", "link_call_log_to_record", "TelephonyRegistry"]
