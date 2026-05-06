# crm/tests/test_telephony_twilio.py
import frappe
from frappe.tests import IntegrationTestCase
from unittest.mock import patch, MagicMock

from crm.integrations.telephony.base import TelephonyProvider
from crm.integrations.telephony.call_linking import CallEvent
from crm.integrations.twilio.twilio_handler import Twilio


class TestTwilioProvider(IntegrationTestCase):
    def test_is_subclass_of_telephony_provider(self):
        from crm.integrations.twilio.twilio_handler import TwilioProvider
        self.assertTrue(issubclass(TwilioProvider, TelephonyProvider))

    def test_provider_name(self):
        from crm.integrations.twilio.twilio_handler import TwilioProvider
        self.assertEqual(TwilioProvider.provider_name, "Twilio")

    def test_parse_webhook_to_event_incoming(self):
        from crm.integrations.twilio.twilio_handler import TwilioProvider

        provider = TwilioProvider.__new__(TwilioProvider)
        provider.enabled = True
        provider.settings = {}

        request_data = {
            "AccountSid": "AC123",
            "CallSid": "CA999",
            "CallStatus": "ringing",
            "Caller": "+14155550100",
            "From": "+14155550100",
            "To": "+14155550200",
        }
        event = provider.parse_webhook_to_event(request_data)

        self.assertIsInstance(event, CallEvent)
        self.assertEqual(event.call_sid, "CA999")
        self.assertEqual(event.direction, "Incoming")
        self.assertEqual(event.status, "Ringing")
        self.assertEqual(event.from_number, "+14155550100")
        self.assertEqual(event.to_number, "+14155550200")
        self.assertEqual(event.telephony_medium, "Twilio")

    def test_parse_webhook_to_event_outgoing(self):
        from crm.integrations.twilio.twilio_handler import TwilioProvider

        provider = TwilioProvider.__new__(TwilioProvider)
        provider.enabled = True
        provider.settings = {}

        request_data = {
            "AccountSid": "AC123",
            "CallSid": "CA888",
            "CallStatus": "in-progress",
            "Caller": "client:admin(at)example.com",
            "From": "+14155550100",
            "To": "+14155550200",
        }
        event = provider.parse_webhook_to_event(request_data)

        self.assertEqual(event.direction, "Outgoing")
        self.assertEqual(event.caller, "admin@example.com")
        self.assertEqual(event.status, "In Progress")

    def test_get_call_status_mapping(self):
        from crm.integrations.twilio.twilio_handler import TwilioProvider

        provider = TwilioProvider.__new__(TwilioProvider)
        provider.enabled = True
        provider.settings = {}

        self.assertEqual(provider.get_call_status("ringing"), "Ringing")
        self.assertEqual(provider.get_call_status("in-progress"), "In Progress")
        self.assertEqual(provider.get_call_status("completed"), "Completed")
        self.assertEqual(provider.get_call_status("no-answer"), "No Answer")

    def test_get_recording_credentials(self):
        from crm.integrations.twilio.twilio_handler import TwilioProvider

        provider = TwilioProvider.__new__(TwilioProvider)
        provider.enabled = True
        provider.settings = {"api_key": "SK123", "api_secret": "secret456"}

        key, secret = provider.get_recording_credentials()
        self.assertEqual(key, "SK123")
        self.assertEqual(secret, "secret456")

    def test_is_enabled_true(self):
        from crm.integrations.twilio.twilio_handler import TwilioProvider
        provider = TwilioProvider.__new__(TwilioProvider)
        provider.enabled = True
        provider.settings = {}
        self.assertTrue(provider.is_enabled())

    def test_is_enabled_false(self):
        from crm.integrations.twilio.twilio_handler import TwilioProvider
        provider = TwilioProvider.__new__(TwilioProvider)
        provider.enabled = False
        provider.settings = {}
        self.assertFalse(provider.is_enabled())

    def test_validate_webhook_checks_application_sid(self):
        from crm.integrations.twilio.twilio_handler import TwilioProvider

        provider = TwilioProvider.__new__(TwilioProvider)
        provider.enabled = True
        provider.settings = {"account_sid": "AC123", "application_sid": "AP456"}

        valid_data = {"AccountSid": "AC123", "ApplicationSid": "AP456"}
        self.assertTrue(provider.validate_webhook(valid_data, require_application_id=True))

        wrong_app = {"AccountSid": "AC123", "ApplicationSid": "AP_WRONG"}
        with self.assertRaises(frappe.PermissionError):
            provider.validate_webhook(wrong_app, require_application_id=True)

        missing_app = {"AccountSid": "AC123"}
        with self.assertRaises(frappe.PermissionError):
            provider.validate_webhook(missing_app, require_application_id=True)

    def test_validate_webhook_skips_application_sid_by_default(self):
        from crm.integrations.twilio.twilio_handler import TwilioProvider

        provider = TwilioProvider.__new__(TwilioProvider)
        provider.enabled = True
        provider.settings = {"account_sid": "AC123", "application_sid": "AP456"}

        data = {"AccountSid": "AC123"}
        self.assertTrue(provider.validate_webhook(data))

    def test_make_outbound_call_returns_outbound_call_result(self):
        from crm.integrations.telephony.base import OutboundCallResult
        from crm.integrations.twilio.twilio_handler import TwilioProvider

        provider = TwilioProvider.__new__(TwilioProvider)
        provider.enabled = True
        provider.settings = {}

        with patch.object(Twilio, 'connect') as mock_connect:
            mock_twilio = MagicMock()
            mock_resp = MagicMock()
            mock_resp.to_xml.return_value = "<Response/>"
            mock_twilio.generate_twilio_dial_response.return_value = mock_resp
            mock_connect.return_value = mock_twilio

            result = provider.make_outbound_call("+1111", "+2222", "test@test.com")
            self.assertIsInstance(result, OutboundCallResult)
            self.assertIsNone(result.call_sid)
            self.assertIn("twiml", result.provider_response)
