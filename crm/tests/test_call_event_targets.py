# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.event import _send_system_notification
from crm.integrations.exotel.handler import publish_call_event
from crm.tests.test_password_setup import make_user


def make_agent(user):
	return frappe.get_doc(doctype="CRM Telephony Agent", user=user).insert(ignore_permissions=True)


class TestExotelCallEventTarget(IntegrationTestCase):
	def setUp(self):
		self.agent = make_user("exotel-agent-46113@example.com", roles=["Sales User"]).name
		self.other = make_user("exotel-other-46113@example.com", roles=["Sales User"]).name
		make_agent(self.agent)
		make_agent(self.other)
		self.request = frappe.local.request if hasattr(frappe.local, "request") else None
		self.set_request_args({})

	def tearDown(self):
		frappe.local.request = self.request
		frappe.db.rollback()

	def set_request_args(self, args):
		frappe.local.request = SimpleNamespace(args=args)

	def publish(self, payload):
		with patch("frappe.publish_realtime") as publish_realtime:
			publish_call_event(payload)
		return publish_realtime

	def test_an_incoming_call_goes_to_its_agent_only(self):
		payload = {"CallSid": "c-46113-in", "Direction": "incoming", "AgentEmail": self.agent}

		publish_realtime = self.publish(payload)

		publish_realtime.assert_called_once_with("exotel_call", payload, user=self.agent)

	def test_the_payload_keeps_the_agent_email_for_the_v1_call_popup(self):
		payload = {"CallSid": "c-46113-v1", "Direction": "incoming", "AgentEmail": self.agent}

		publish_realtime = self.publish(payload)

		self.assertEqual(publish_realtime.call_args.args[1]["AgentEmail"], self.agent)

	def test_an_outgoing_call_goes_to_the_agent_in_the_callback_url(self):
		self.set_request_args({"agent": self.agent})
		payload = {"CallSid": "c-46113-out", "Direction": "outbound-api"}

		publish_realtime = self.publish(payload)

		publish_realtime.assert_called_once_with("exotel_call", payload, user=self.agent)

	def test_a_later_event_without_an_agent_goes_to_the_call_logs_agent(self):
		call_log = frappe.new_doc("CRM Call Log")
		call_log.update({"id": "c-46113-log", "type": "Incoming", "receiver": self.agent, "to": "+911"})
		setattr(call_log, "from", "+912")
		call_log.insert(ignore_permissions=True)
		payload = {"CallSid": "c-46113-log", "Status": "completed"}

		publish_realtime = self.publish(payload)

		publish_realtime.assert_called_once_with("exotel_call", payload, user=self.agent)

	def test_a_payload_with_no_agent_goes_to_nobody_and_is_logged(self):
		payload = {"CallSid": "c-46113-none", "Direction": "incoming", "CallFrom": "+911234567890"}

		with patch("frappe.log_error") as log_error:
			publish_realtime = self.publish(payload)

		publish_realtime.assert_not_called()
		log_error.assert_called_once()
		self.assertIn("c-46113-none", log_error.call_args.kwargs["message"])
		self.assertNotIn("911234567890", log_error.call_args.kwargs["message"])

	def test_an_agent_that_is_not_a_telephony_agent_goes_to_nobody(self):
		stranger = make_user("exotel-stranger-46113@example.com", roles=["Sales User"]).name
		payload = {"CallSid": "c-46113-stranger", "AgentEmail": stranger}

		with patch("frappe.log_error"):
			publish_realtime = self.publish(payload)

		publish_realtime.assert_not_called()


class TestEventReminderTarget(IntegrationTestCase):
	def setUp(self):
		self.owner = make_user("event-owner-46113@example.com", roles=["Sales User"]).name
		self.participant = make_user("event-guest-46113@example.com", roles=["Sales User"]).name
		self.bystander = make_user("event-bystander-46113@example.com", roles=["Sales User"]).name

	def tearDown(self):
		frappe.db.rollback()

	def send(self, **notification):
		with patch("frappe.publish_realtime") as publish_realtime:
			_send_system_notification(frappe._dict(notification))
		return publish_realtime

	def recipients(self, publish_realtime):
		return {call.kwargs["user"] for call in publish_realtime.call_args_list}

	def test_a_reminder_goes_to_the_owner_and_the_participants_who_are_users(self):
		publish_realtime = self.send(
			owner=self.owner, event_participants=[self.participant, "customer-46113@example.org"]
		)

		self.assertEqual(self.recipients(publish_realtime), {self.owner, self.participant})
		self.assertNotIn(self.bystander, self.recipients(publish_realtime))

	def test_a_reminder_skips_a_disabled_participant(self):
		frappe.db.set_value("User", self.participant, "enabled", 0)

		publish_realtime = self.send(owner=self.owner, event_participants=[self.participant])

		self.assertEqual(self.recipients(publish_realtime), {self.owner})

	def test_a_reminder_with_no_participants_goes_to_the_owner(self):
		publish_realtime = self.send(owner=self.owner, event_participants=[])

		self.assertEqual(self.recipients(publish_realtime), {self.owner})
