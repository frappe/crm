# crm/tests/test_telephony_exotel.py
import frappe
from frappe.tests import IntegrationTestCase

from crm.integrations.telephony.base import TelephonyProvider
from crm.integrations.telephony.call_linking import CallEvent


class TestExotelProvider(IntegrationTestCase):
    def test_is_subclass_of_telephony_provider(self):
        from crm.integrations.exotel.handler import ExotelProvider
        self.assertTrue(issubclass(ExotelProvider, TelephonyProvider))

    def test_provider_name(self):
        from crm.integrations.exotel.handler import ExotelProvider
        self.assertEqual(ExotelProvider.provider_name, "Exotel")

    def test_parse_webhook_to_event_incoming(self):
        from crm.integrations.exotel.handler import ExotelProvider

        provider = ExotelProvider.__new__(ExotelProvider)
        provider.enabled = True
        provider.settings = {}

        request_data = {
            "CallSid": "exo123",
            "CallFrom": "+919876543210",
            "DialWhomNumber": "+14155550200",
            "CallType": "completed",
            "DialCallStatus": "completed",
            "Status": "completed",
            "To": "+14155550300",
            "AgentEmail": "agent@example.com",
            "Direction": "incoming",
        }
        event = provider.parse_webhook_to_event(request_data)

        self.assertIsInstance(event, CallEvent)
        self.assertEqual(event.call_sid, "exo123")
        self.assertEqual(event.direction, "Incoming")
        self.assertEqual(event.from_number, "+919876543210")
        self.assertEqual(event.to_number, "+14155550200")
        self.assertEqual(event.receiver, "agent@example.com")
        self.assertEqual(event.telephony_medium, "Exotel")

    def test_get_call_status_completed(self):
        from crm.integrations.exotel.handler import ExotelProvider

        provider = ExotelProvider.__new__(ExotelProvider)
        provider.enabled = True
        provider.settings = {}

        self.assertEqual(provider.get_call_status("completed"), "Completed")

    def test_get_call_status_busy(self):
        from crm.integrations.exotel.handler import ExotelProvider

        provider = ExotelProvider.__new__(ExotelProvider)
        provider.enabled = True
        provider.settings = {}

        self.assertEqual(provider.get_call_status("busy"), "Ringing")

    def test_get_call_status_no_answer(self):
        from crm.integrations.exotel.handler import ExotelProvider

        provider = ExotelProvider.__new__(ExotelProvider)
        provider.enabled = True
        provider.settings = {}

        self.assertEqual(provider.get_call_status("no-answer"), "No Answer")

    def test_get_call_status_failed(self):
        from crm.integrations.exotel.handler import ExotelProvider

        provider = ExotelProvider.__new__(ExotelProvider)
        provider.enabled = True
        provider.settings = {}

        self.assertEqual(provider.get_call_status("failed"), "Failed")

    def test_get_recording_credentials(self):
        from crm.integrations.exotel.handler import ExotelProvider

        provider = ExotelProvider.__new__(ExotelProvider)
        provider.enabled = True
        provider.settings = {"api_key": "exokey", "api_token": "exosecret"}

        key, secret = provider.get_recording_credentials()
        self.assertEqual(key, "exokey")
        self.assertEqual(secret, "exosecret")

    def test_is_enabled(self):
        from crm.integrations.exotel.handler import ExotelProvider
        provider = ExotelProvider.__new__(ExotelProvider)
        provider.enabled = True
        provider.settings = {}
        self.assertTrue(provider.is_enabled())

    def test_is_disabled(self):
        from crm.integrations.exotel.handler import ExotelProvider
        provider = ExotelProvider.__new__(ExotelProvider)
        provider.enabled = False
        provider.settings = {}
        self.assertFalse(provider.is_enabled())

    def test_parse_webhook_to_event_outbound_api_payload(self):
        """Exotel outbound API responses use Sid/From/To instead of CallSid/CallFrom/DialWhomNumber"""
        from crm.integrations.exotel.handler import ExotelProvider

        provider = ExotelProvider.__new__(ExotelProvider)
        provider.enabled = True
        provider.settings = {}

        request_data = {
            "Sid": "exo_out_456",
            "From": "+919876543210",
            "To": "+14155550200",
            "PhoneNumberSid": "0401234567",
            "Status": "completed",
            "Direction": "outbound-api",
        }
        event = provider.parse_webhook_to_event(request_data)

        self.assertIsInstance(event, CallEvent)
        self.assertEqual(event.call_sid, "exo_out_456")
        self.assertEqual(event.direction, "Outgoing")
        self.assertEqual(event.from_number, "+919876543210")
        self.assertEqual(event.to_number, "+14155550200")
        self.assertEqual(event.telephony_medium, "Exotel")

    def test_parse_webhook_to_event_outbound_dial_payload(self):
        """Exotel outbound-dial callbacks"""
        from crm.integrations.exotel.handler import ExotelProvider

        provider = ExotelProvider.__new__(ExotelProvider)
        provider.enabled = True
        provider.settings = {}

        request_data = {
            "CallSid": "exo_dial_789",
            "CallFrom": "+919876543210",
            "DialWhomNumber": "+14155550200",
            "Status": "in-progress",
            "Direction": "outbound-dial",
            "DialCallDuration": "45",
        }
        event = provider.parse_webhook_to_event(request_data)

        self.assertEqual(event.call_sid, "exo_dial_789")
        self.assertEqual(event.direction, "Outgoing")
        self.assertEqual(event.from_number, "+919876543210")
        self.assertEqual(event.duration, 45)

    def test_parse_webhook_null_call_sid_fallback(self):
        """When neither CallSid nor Sid is present, call_sid should be None"""
        from crm.integrations.exotel.handler import ExotelProvider

        provider = ExotelProvider.__new__(ExotelProvider)
        provider.enabled = True
        provider.settings = {}

        request_data = {
            "Status": "free",
            "Direction": "incoming",
        }
        event = provider.parse_webhook_to_event(request_data)

        self.assertIsNone(event.call_sid)
