from dataclasses import dataclass, field

import frappe

from crm.integrations.api import get_contact_by_phone_number


@dataclass
class CallEvent:
    call_sid: str
    direction: str  # "Incoming" or "Outgoing"
    status: str
    from_number: str
    to_number: str
    caller: str  # user email for outgoing calls
    receiver: str  # user email for incoming calls
    telephony_medium: str
    duration: int | None = None
    recording_url: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    medium: str | None = None  # phone number SID / exophone

    @property
    def contact_number(self) -> str:
        return self.from_number if self.direction == "Incoming" else self.to_number

    def to_call_log_dict(self) -> dict:
        return {
            "doctype": "CRM Call Log",
            "id": self.call_sid,
            "type": self.direction,
            "status": self.status,
            "from": self.from_number,
            "to": self.to_number,
            "caller": self.caller,
            "receiver": self.receiver,
            "telephony_medium": self.telephony_medium,
            "duration": self.duration,
            "recording_url": self.recording_url or "",
            "start_time": self.start_time,
            "end_time": self.end_time,
            "medium": self.medium,
        }


def link_call_log_to_record(call_log, contact_number: str):
    contact = get_contact_by_phone_number(contact_number)
    if contact.get("name"):
        doctype = "Contact"
        docname = contact.get("name")
        if contact.get("lead"):
            doctype = "CRM Lead"
            docname = contact.get("lead")
        elif contact.get("deal"):
            doctype = "CRM Deal"
            docname = contact.get("deal")
        call_log.link_with_reference_doc(doctype, docname)
