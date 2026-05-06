# crm/tests/test_telephony_registry.py
import frappe
from frappe.tests import IntegrationTestCase
from unittest.mock import patch

from crm.integrations.telephony.base import TelephonyProvider
from crm.integrations.telephony.call_linking import CallEvent


class FakeProvider(TelephonyProvider):
	provider_name = "Fake"

	def validate_webhook(self, request_data, require_application_id=False):
		return True

	def parse_webhook_to_event(self, request_data):
		return CallEvent(
			call_sid="F1", direction="Incoming", status="Ringing",
			from_number="+1111", to_number="+2222",
			caller="", receiver="test@test.com", telephony_medium="Fake",
		)

	def make_outbound_call(self, from_number, to_number, caller_user):
		from crm.integrations.telephony.base import OutboundCallResult
		return OutboundCallResult(call_sid="F1", provider_response={})

	def get_recording_credentials(self):
		return ("k", "s")

	def get_call_status(self, raw_status):
		return "Completed"

	def is_enabled(self):
		return self.enabled


class TestTelephonyRegistry(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()
		from crm.integrations.telephony.registry import TelephonyRegistry
		TelephonyRegistry._clear_cache()

	def test_get_provider_by_name(self):
		from crm.integrations.telephony.registry import TelephonyRegistry
		TelephonyRegistry.register(FakeProvider(enabled=True, settings={}))

		provider = TelephonyRegistry.get_provider("Fake")
		self.assertIsNotNone(provider)
		self.assertEqual(provider.provider_name, "Fake")

	def test_get_provider_returns_none_for_unknown(self):
		from crm.integrations.telephony.registry import TelephonyRegistry
		provider = TelephonyRegistry.get_provider("NonExistent")
		self.assertIsNone(provider)

	def test_get_enabled_providers(self):
		from crm.integrations.telephony.registry import TelephonyRegistry
		TelephonyRegistry.register(FakeProvider(enabled=True, settings={}))

		enabled = TelephonyRegistry.get_enabled_providers()
		self.assertEqual(len(enabled), 1)
		self.assertEqual(enabled[0].provider_name, "Fake")

	def test_disabled_provider_not_in_enabled_list(self):
		from crm.integrations.telephony.registry import TelephonyRegistry
		TelephonyRegistry.register(FakeProvider(enabled=False, settings={}))

		enabled = TelephonyRegistry.get_enabled_providers()
		self.assertEqual(len(enabled), 0)

	def test_get_recording_credentials_by_medium(self):
		from crm.integrations.telephony.registry import TelephonyRegistry
		TelephonyRegistry.register(FakeProvider(enabled=True, settings={}))

		key, secret = TelephonyRegistry.get_recording_credentials("Fake")
		self.assertEqual(key, "k")
		self.assertEqual(secret, "s")

	def test_get_recording_credentials_unknown_raises(self):
		from crm.integrations.telephony.registry import TelephonyRegistry
		with self.assertRaises(frappe.ValidationError):
			TelephonyRegistry.get_recording_credentials("Unknown")

	def test_discover_from_settings(self):
		from crm.integrations.telephony.registry import TelephonyRegistry

		frappe.db.set_single_value("CRM Twilio Settings", "enabled", 0)
		frappe.db.set_single_value("CRM Exotel Settings", "enabled", 0)

		TelephonyRegistry.discover()
		enabled = TelephonyRegistry.get_enabled_providers()
		self.assertEqual(len(enabled), 0)

	def test_is_any_provider_enabled_false(self):
		from crm.integrations.telephony.registry import TelephonyRegistry
		frappe.db.set_single_value("CRM Twilio Settings", "enabled", 0)
		frappe.db.set_single_value("CRM Exotel Settings", "enabled", 0)
		TelephonyRegistry.discover()
		self.assertFalse(TelephonyRegistry.is_any_enabled())

	def test_status_summary(self):
		from crm.integrations.telephony.registry import TelephonyRegistry
		TelephonyRegistry.register(FakeProvider(enabled=True, settings={}))

		summary = TelephonyRegistry.status_summary()
		self.assertIn("Fake", summary)
		self.assertTrue(summary["Fake"])

	def test_discover_logs_error_on_provider_failure(self):
		"""Discovery failures are logged, not silently swallowed"""
		from crm.integrations.telephony.registry import TelephonyRegistry
		from unittest.mock import patch

		error_log_count_before = frappe.db.count("Error Log", {"method": ["like", "%Telephony provider%"]})

		with patch(
			"crm.integrations.telephony.registry.TelephonyRegistry._discover_provider"
		) as mock_discover:
			mock_discover.side_effect = None
			TelephonyRegistry.discover()

		# Test the actual _discover_provider with a broken module
		TelephonyRegistry._discover_provider(
			"Broken", "crm.integrations.nonexistent_module", "BrokenProvider"
		)

		error_log_count_after = frappe.db.count("Error Log", {"method": ["like", "%Telephony provider%"]})
		self.assertGreater(error_log_count_after, error_log_count_before)
