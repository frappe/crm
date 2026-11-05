from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.fcrm.doctype.crm_dashboard import ask_flow
from crm.tests.test_home import AGENT, make_user


class TestAskFlow(IntegrationTestCase):
	def setUp(self):
		make_user(AGENT, "Sales User")
		self.api = MagicMock()
		self.api.create_session.return_value = {"name": "session-1"}
		modules = {"frappe.flow.api": self.api}
		patcher = patch.dict("sys.modules", modules)
		patcher.start()
		self.addCleanup(patcher.stop)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def available(self, value=True):
		return patch.object(ask_flow, "flow_available", return_value=value)

	def test_a_chat_starts_in_ask_mode_and_runs_the_message(self):
		frappe.set_user(AGENT)
		with self.available(), patch.object(ask_flow, "grant_flow_role"):
			session = ask_flow.start_flow_chat("Draft my replies")
		self.assertEqual(session, "session-1")
		self.api.create_session.assert_called_once_with(approval_mode="Ask")
		self.api.run.assert_called_once_with("session-1", "Draft my replies")

	def test_no_chat_when_flow_is_missing(self):
		with self.available(False), self.assertRaises(frappe.ValidationError):
			ask_flow.start_flow_chat("Draft my replies")
		self.api.create_session.assert_not_called()

	def test_an_empty_message_is_refused(self):
		with self.available(), self.assertRaises(frappe.ValidationError):
			ask_flow.start_flow_chat("   ")

	def test_a_user_with_the_role_is_left_alone(self):
		with patch.object(frappe, "get_roles", return_value=[ask_flow.FLOW_ROLE]):
			with patch.object(frappe, "get_doc") as get_doc:
				ask_flow.grant_flow_role(AGENT)
		get_doc.assert_not_called()

	def test_no_provider_means_not_available(self):
		frappe.db.set_value("Flow Provider", {"enabled": 1}, "enabled", 0)
		self.assertFalse(ask_flow.flow_available())
