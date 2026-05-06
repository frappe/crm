from crm.integrations.telephony.base import OutboundCallResult, TelephonyProvider
from crm.integrations.telephony.call_linking import CallEvent, link_call_log_to_record
from crm.integrations.telephony.registry import TelephonyRegistry

__all__ = ["CallEvent", "OutboundCallResult", "TelephonyProvider", "TelephonyRegistry", "link_call_log_to_record"]
