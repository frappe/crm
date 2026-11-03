# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.integrations.exotel import handler
from crm.integrations.telephony_mock import dev, exotel
from crm.integrations.telephony_mock import twilio as twilio_mock
from crm.integrations.telephony_mock.mode import MOCK_TWILIO_TOKEN, is_mock_mode
from crm.integrations.twilio.api import generate_access_token
from crm.tests.test_password_setup import make_user

MOCK_ON = {"developer_mode": 1, "crm_telephony_mock": 1}


class TestTelephonyMockMode(IntegrationTestCase):
	def test_mock_mode_needs_both_the_flag_and_developer_mode(self):
		for conf, expected in (
			({"developer_mode": 0, "crm_telephony_mock": 1}, False),
			({"developer_mode": 1, "crm_telephony_mock": 0}, False),
			({"developer_mode": 1}, False),
			(MOCK_ON, True),
		):
			with patch.dict(frappe.conf, conf, clear=False):
				for key in set(MOCK_ON) - set(conf):
					frappe.conf.pop(key, None)
				self.assertEqual(is_mock_mode(), expected, conf)

	def test_the_twilio_token_is_real_code_when_developer_mode_is_off(self):
		with (
			patch.dict(frappe.conf, {"developer_mode": 0, "crm_telephony_mock": 1}),
			patch("crm.integrations.twilio.api.Twilio.connect", return_value=None) as connect,
		):
			self.assertEqual(generate_access_token(), {})

		connect.assert_called_once()

	def test_the_twilio_token_is_a_dummy_in_mock_mode(self):
		with patch.dict(frappe.conf, MOCK_ON):
			self.assertEqual(generate_access_token(), {"token": MOCK_TWILIO_TOKEN, "mock": True})

	def test_setup_refuses_to_overwrite_real_credentials(self):
		with (
			patch.dict(frappe.conf, MOCK_ON),
			patch("frappe.db.get_single_value", return_value="AC-real-account"),
			patch("frappe.db.set_single_value") as write,
		):
			with self.assertRaises(frappe.ValidationError):
				dev.setup_walk()

		write.assert_not_called()

	def test_setup_refuses_to_overwrite_a_real_agent_row(self):
		user = make_user("exotel-mock-real-46112@example.com", roles=["Sales User"]).name
		frappe.get_doc(doctype="CRM Telephony Agent", user=user, mobile_no="+919812345678").insert(
			ignore_permissions=True
		)
		self.addCleanup(frappe.db.rollback)
		with patch.dict(frappe.conf, MOCK_ON), self.assertRaises(frappe.ValidationError):
			dev.setup_walk(user=user)

	def test_the_dev_helpers_refuse_when_mock_mode_is_off(self):
		with patch.dict(frappe.conf, {"developer_mode": 0, "crm_telephony_mock": 1}):
			with self.assertRaises(frappe.PermissionError):
				dev.setup_walk()
			with self.assertRaises(frappe.PermissionError):
				dev.ring_exotel()

	def test_exotel_posts_to_the_api_when_mock_mode_is_off(self):
		with (
			patch.dict(frappe.conf, {"developer_mode": 0, "crm_telephony_mock": 1}),
			patch.object(handler, "is_integration_enabled", return_value=1),
			patch.object(handler, "get_exotel_endpoint", return_value="https://exotel.invalid"),
			patch.object(handler, "get_all_exophones", return_value=["+918880000001"]),
			patch.object(handler, "get_status_updater_url", return_value="https://x.invalid"),
			patch.object(handler.requests, "post", side_effect=RuntimeError("real HTTP")) as post,
			patch("frappe.db.get_single_value", return_value=0),
			patch("frappe.get_value", return_value="+918880000001"),
		):
			with self.assertRaises(RuntimeError):
				handler.make_a_call("+915550100101", from_number="+919999900001")

		post.assert_called_once()


class TestExotelMock(IntegrationTestCase):
	def setUp(self):
		self.agent = make_user("exotel-mock-agent-46112@example.com", roles=["Sales User"]).name
		self.other = make_user("exotel-mock-other-46112@example.com", roles=["Sales User"]).name
		self.patches = [
			patch.dict(frappe.conf, MOCK_ON),
			patch("frappe.db.commit"),
		]
		for p in self.patches:
			p.start()
		dev.setup_walk(user=self.agent)
		dev.setup_walk(user=self.other)

	def tearDown(self):
		for p in reversed(self.patches):
			p.stop()
		frappe.db.rollback()

	def published(self):
		return patch("frappe.publish_realtime")

	def call_events(self, publish_realtime):
		"""The `(payload, user)` of each `exotel_call` event, apart from doc and list updates."""
		return [
			(c.args[1], c.kwargs.get("user"))
			for c in publish_realtime.call_args_list
			if c.args[0] == "exotel_call"
		]

	def test_an_inbound_replay_reaches_only_its_agent(self):
		with self.published() as publish_realtime:
			payload = exotel.ring_inbound(agent=self.agent, from_number="+915550100177")

		self.assertEqual(self.call_events(publish_realtime), [(payload, self.agent)])

	def test_an_inbound_replay_makes_the_call_log_through_the_real_handler(self):
		with self.published():
			payload = exotel.ring_inbound(agent=self.agent)

		call_log = frappe.get_doc("CRM Call Log", payload["CallSid"])
		self.assertEqual(
			(call_log.type, call_log.receiver, call_log.status), ("Incoming", self.agent, "Ringing")
		)
		self.assertEqual(call_log.telephony_medium, "Exotel")

	def test_a_later_inbound_event_updates_the_log_and_still_reaches_only_its_agent(self):
		with self.published():
			sid = exotel.ring_inbound(agent=self.agent)["CallSid"]
		with self.published() as publish_realtime:
			exotel.send_event(sid, "inbound_completed")

		self.assertEqual(frappe.db.get_value("CRM Call Log", sid, "status"), "Completed")
		self.assertEqual([user for _payload, user in self.call_events(publish_realtime)], [self.agent])

	def test_an_outbound_call_posts_no_http_and_calls_back_to_its_agent(self):
		frappe.set_user(self.agent)
		self.addCleanup(frappe.set_user, "Administrator")
		with (
			self.published() as publish_realtime,
			patch.object(handler.requests, "post", side_effect=RuntimeError("real HTTP")),
		):
			call = handler.make_a_call("+915550100177")

		call_log = frappe.get_doc("CRM Call Log", call["CallSid"])
		self.assertEqual(
			(call_log.type, call_log.caller, call_log.status), ("Outgoing", self.agent, "In Progress")
		)
		events = self.call_events(publish_realtime)
		self.assertEqual([user for _payload, user in events], [self.agent])
		self.assertEqual(events[0][0]["Legs[1][Status]"], "")

	def test_an_outbound_terminal_event_completes_the_log(self):
		frappe.set_user(self.agent)
		self.addCleanup(frappe.set_user, "Administrator")
		with self.published():
			sid = handler.make_a_call("+915550100177")["CallSid"]
			exotel.send_event(sid, "outbound_completed")

		self.assertEqual(frappe.db.get_value("CRM Call Log", sid, "status"), "Completed")


class TestTelephonyDevHelpers(IntegrationTestCase):
	def setUp(self):
		self.user = make_user("exotel-mock-dev-46112@example.com", roles=["Sales User"]).name
		self.patches = [patch.dict(frappe.conf, MOCK_ON), patch("frappe.db.commit")]
		for p in self.patches:
			p.start()

	def tearDown(self):
		for p in reversed(self.patches):
			p.stop()
		frappe.db.rollback()

	def test_setup_twice_then_teardown_leaves_a_blank_agent_and_disabled_settings(self):
		dev.setup_walk(user=self.user)
		dev.setup_walk(user=self.user)
		self.assertEqual(frappe.db.get_single_value("CRM Exotel Settings", "enabled"), 1)
		dev.teardown_walk(user=self.user)

		agent = frappe.db.get_value("CRM Telephony Agent", self.user, ["twilio_number", "exotel_number"])
		self.assertEqual(agent, ("", ""))
		self.assertEqual(frappe.db.get_single_value("CRM Twilio Settings", "enabled"), 0)
		self.assertFalse(frappe.db.get_single_value("CRM Exotel Settings", "webhook_verify_token"))

	def test_the_webhook_key_is_not_the_same_on_every_site(self):
		dev.setup_walk(user=self.user)
		first = frappe.db.get_single_value("CRM Exotel Settings", "webhook_verify_token")
		dev.setup_walk(user=self.user)

		self.assertTrue(first)
		self.assertNotEqual(first, frappe.db.get_single_value("CRM Exotel Settings", "webhook_verify_token"))

	def test_a_replay_refuses_a_call_that_is_not_a_mock_exotel_call(self):
		dev.setup_walk(user=self.user)
		call_log = frappe.new_doc("CRM Call Log")
		call_log.update({"id": "real-46112", "type": "Incoming", "receiver": self.user, "to": "+911"})
		setattr(call_log, "from", "+912")
		call_log.insert(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			exotel.send_event("real-46112", "inbound_completed")

	def test_the_whitelisted_helpers_need_system_manager(self):
		frappe.set_user(self.user)
		self.addCleanup(frappe.set_user, "Administrator")
		for helper in (lambda: dev.ring_exotel(), lambda: dev.record_twilio_call("+15550100177")):
			with self.assertRaises(frappe.PermissionError):
				helper()

	def test_a_twilio_call_log_is_made_by_the_real_code(self):
		dev.setup_walk(user=self.user)
		frappe.set_user(self.user)
		self.addCleanup(frappe.set_user, "Administrator")
		sid = twilio_mock.record_call(self.user, "+15550100177")

		call_log = frappe.get_doc("CRM Call Log", sid)
		self.assertEqual(
			(call_log.type, call_log.caller, call_log.telephony_medium), ("Outgoing", self.user, "Twilio")
		)
		with self.assertRaises(frappe.ValidationError):
			twilio_mock.record_call(self.user, "+15550100177", "Outgoin")
