# crm/tests/test_telephony_base.py
import frappe
from frappe.tests import IntegrationTestCase

from crm.integrations.telephony.call_linking import CallEvent, link_call_log_to_record


class TestCallEvent(IntegrationTestCase):
    def test_call_event_incoming(self):
        event = CallEvent(
            call_sid="CA123",
            direction="Incoming",
            status="Ringing",
            from_number="+14155550100",
            to_number="+14155550200",
            caller="",
            receiver="admin@example.com",
            telephony_medium="Twilio",
        )
        self.assertEqual(event.call_sid, "CA123")
        self.assertEqual(event.direction, "Incoming")
        self.assertEqual(event.contact_number, "+14155550100")

    def test_call_event_outgoing(self):
        event = CallEvent(
            call_sid="CA456",
            direction="Outgoing",
            status="Ringing",
            from_number="+14155550100",
            to_number="+14155550200",
            caller="admin@example.com",
            receiver="",
            telephony_medium="Exotel",
        )
        self.assertEqual(event.contact_number, "+14155550200")

    def test_call_event_to_call_log_dict(self):
        event = CallEvent(
            call_sid="CA789",
            direction="Incoming",
            status="Completed",
            from_number="+14155550100",
            to_number="+14155550200",
            caller="",
            receiver="admin@example.com",
            telephony_medium="Twilio",
        )
        d = event.to_call_log_dict()
        self.assertEqual(d["doctype"], "CRM Call Log")
        self.assertEqual(d["id"], "CA789")
        self.assertEqual(d["type"], "Incoming")
        self.assertEqual(d["status"], "Completed")
        self.assertEqual(d["from"], "+14155550100")
        self.assertEqual(d["to"], "+14155550200")
        self.assertEqual(d["telephony_medium"], "Twilio")
        self.assertEqual(d["receiver"], "admin@example.com")
        self.assertEqual(d["caller"], "")


class TestLinkCallLogToRecord(IntegrationTestCase):
    def tearDown(self):
        frappe.db.rollback()

    def test_link_to_lead(self):
        lead = frappe.get_doc({
            "doctype": "CRM Lead",
            "first_name": "Link",
            "last_name": "Test",
            "mobile_no": "+91 98765 43210",
            "lead_owner": "Administrator",
        }).insert()

        import uuid
        call_log = frappe.get_doc({
            "doctype": "CRM Call Log",
            "id": str(uuid.uuid4())[:10],
            "type": "Incoming",
            "status": "Completed",
            "from": "+91 98765 43210",
            "to": "+14155550100",
        }).insert()

        link_call_log_to_record(call_log, "+91 98765 43210")
        call_log.save(ignore_permissions=True)

        call_log.reload()
        linked = [l for l in call_log.links if l.link_doctype == "CRM Lead"]
        self.assertEqual(len(linked), 1)
        self.assertEqual(linked[0].link_name, lead.name)

    def test_link_no_match_does_nothing(self):
        import uuid
        call_log = frappe.get_doc({
            "doctype": "CRM Call Log",
            "id": str(uuid.uuid4())[:10],
            "type": "Incoming",
            "status": "Completed",
            "from": "+19999999999",
            "to": "+14155550100",
        }).insert()

        link_call_log_to_record(call_log, "+19999999999")
        call_log.save(ignore_permissions=True)

        call_log.reload()
        self.assertEqual(len(call_log.links), 0)


from crm.integrations.telephony.base import OutboundCallResult, TelephonyProvider


class TestTelephonyProviderContract(IntegrationTestCase):
    def test_cannot_instantiate_abstract(self):
        with self.assertRaises(TypeError):
            TelephonyProvider(enabled=True, settings={})

    def test_concrete_must_implement_all_methods(self):
        class IncompleteProvider(TelephonyProvider):
            provider_name = "Incomplete"
        with self.assertRaises(TypeError):
            IncompleteProvider(enabled=True, settings={})

    def test_concrete_with_all_methods_works(self):
        class FakeProvider(TelephonyProvider):
            provider_name = "Fake"

            def validate_webhook(self, request_data, require_application_id=False):
                return True

            def parse_webhook_to_event(self, request_data):
                return CallEvent(
                    call_sid="FAKE1",
                    direction="Incoming",
                    status="Ringing",
                    from_number="+1111",
                    to_number="+2222",
                    caller="",
                    receiver="test@test.com",
                    telephony_medium="Fake",
                )

            def make_outbound_call(self, from_number, to_number, caller_user):
                return OutboundCallResult(call_sid="FAKE_OUT", provider_response={})

            def get_recording_credentials(self):
                return ("key", "secret")

            def get_call_status(self, raw_status):
                return "Completed"

            def is_enabled(self):
                return self.enabled

        provider = FakeProvider(enabled=True, settings={"api_key": "test"})
        self.assertTrue(provider.is_enabled())
        self.assertEqual(provider.provider_name, "Fake")
        result = provider.make_outbound_call("+1111", "+2222", "test@test.com")
        self.assertEqual(result.call_sid, "FAKE_OUT")
        self.assertIsInstance(result, OutboundCallResult)
