# crm/tests/test_telephony_integration.py
import uuid

import frappe
from frappe.tests import IntegrationTestCase

from crm.integrations.telephony import CallEvent, TelephonyRegistry, link_call_log_to_record


class TestTelephonyIntegration(IntegrationTestCase):
    def tearDown(self):
        frappe.db.rollback()
        TelephonyRegistry._clear_cache()

    def test_call_event_to_call_log_with_linking(self):
        """Full flow: CallEvent -> CRM Call Log -> linked to CRM Lead"""
        lead = frappe.get_doc({
            "doctype": "CRM Lead",
            "first_name": "Integration",
            "last_name": "Test",
            "mobile_no": "+91 98765 43210",
            "lead_owner": "Administrator",
        }).insert()

        event = CallEvent(
            call_sid=str(uuid.uuid4())[:10],
            direction="Incoming",
            status="Completed",
            from_number="+91 98765 43210",
            to_number="+14155550200",
            caller="",
            receiver="Administrator",
            telephony_medium="Twilio",
        )

        call_log = frappe.get_doc(event.to_call_log_dict())
        link_call_log_to_record(call_log, event.contact_number)
        call_log.insert(ignore_permissions=True)

        call_log.reload()
        linked_leads = [l for l in call_log.links if l.link_doctype == "CRM Lead"]
        self.assertEqual(len(linked_leads), 1)
        self.assertEqual(linked_leads[0].link_name, lead.name)

    def test_registry_discover_with_both_disabled(self):
        """Registry discover with both providers disabled returns empty"""
        frappe.db.set_single_value("CRM Twilio Settings", "enabled", 0)
        frappe.db.set_single_value("CRM Exotel Settings", "enabled", 0)

        TelephonyRegistry.discover()
        self.assertFalse(TelephonyRegistry.is_any_enabled())
        self.assertEqual(len(TelephonyRegistry.get_enabled_providers()), 0)

    def test_recording_credentials_unknown_medium_raises(self):
        """Requesting credentials for unknown medium raises ValidationError"""
        TelephonyRegistry.discover()
        with self.assertRaises(frappe.ValidationError):
            TelephonyRegistry.get_recording_credentials("SomeUnknownProvider")

    def test_call_event_contact_number_incoming(self):
        """For incoming calls, contact_number is the from_number"""
        event = CallEvent(
            call_sid="test1", direction="Incoming", status="Ringing",
            from_number="+1111", to_number="+2222",
            caller="", receiver="agent@test.com", telephony_medium="Test",
        )
        self.assertEqual(event.contact_number, "+1111")

    def test_call_event_contact_number_outgoing(self):
        """For outgoing calls, contact_number is the to_number"""
        event = CallEvent(
            call_sid="test2", direction="Outgoing", status="Ringing",
            from_number="+1111", to_number="+2222",
            caller="agent@test.com", receiver="", telephony_medium="Test",
        )
        self.assertEqual(event.contact_number, "+2222")

    def test_call_event_to_dict_roundtrip(self):
        """CallEvent -> dict -> CRM Call Log preserves all fields"""
        event = CallEvent(
            call_sid="roundtrip1",
            direction="Outgoing",
            status="Completed",
            from_number="+14155550100",
            to_number="+14155550200",
            caller="admin@example.com",
            receiver="",
            telephony_medium="Exotel",
            duration=120,
            recording_url="https://example.com/recording.mp3",
        )

        d = event.to_call_log_dict()
        call_log = frappe.get_doc(d)
        call_log.insert(ignore_permissions=True)

        call_log.reload()
        self.assertEqual(call_log.id, "roundtrip1")
        self.assertEqual(call_log.type, "Outgoing")
        self.assertEqual(call_log.status, "Completed")
        self.assertEqual(call_log.caller, "admin@example.com")
        self.assertEqual(call_log.telephony_medium, "Exotel")
        self.assertEqual(call_log.duration, 120)
