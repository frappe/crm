from unittest.mock import patch

from frappe.tests import IntegrationTestCase

from crm.api.event import _send_system_notification


class TestEventSystemNotification(IntegrationTestCase):
	def _recipients(self, **notification):
		with patch("frappe.publish_realtime") as publish:
			_send_system_notification({"event_name": "EV-TEST", **notification})
		return {call.kwargs["user"] for call in publish.call_args_list}

	def test_goes_to_the_owner_and_participants_only(self):
		self.assertEqual(
			self._recipients(owner="owner@example.com", event_participants=["guest@example.com"]),
			{"owner@example.com", "guest@example.com"},
		)
