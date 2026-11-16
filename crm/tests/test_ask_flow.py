from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.user import FLOW_ROLE, update_user_role
from crm.fcrm.doctype.crm_dashboard import ask_flow
from crm.patches.v1_0.give_sales_users_flow_role import execute as give_sales_users_flow_role
from crm.tests.test_home import AGENT, make_user
from crm.tests.test_user_role_profile import make_user as make_plain_user
from crm.tests.test_user_role_profile import user_roles


class TestAskFlow(IntegrationTestCase):
	def setUp(self):
		make_user(AGENT, "Sales User")
		frappe.get_doc("User", AGENT).remove_roles(FLOW_ROLE)
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
		with self.available():
			session = ask_flow.start_flow_chat("Draft my replies")
		self.assertEqual(session, "session-1")
		self.api.create_session.assert_called_once_with(approval_mode="Ask")
		self.api.run.assert_called_once_with("session-1", "Draft my replies")

	def test_starting_a_chat_gives_no_role(self):
		frappe.set_user(AGENT)
		with self.available():
			ask_flow.start_flow_chat("Draft my replies")
		self.assertNotIn(FLOW_ROLE, frappe.get_roles(AGENT))

	def test_no_chat_when_flow_is_missing(self):
		with self.available(False), self.assertRaises(frappe.ValidationError):
			ask_flow.start_flow_chat("Draft my replies")
		self.api.create_session.assert_not_called()

	def test_an_empty_message_is_refused(self):
		with self.available(), self.assertRaises(frappe.ValidationError):
			ask_flow.start_flow_chat("   ")

	def flow_enabled(self, value=True):
		return patch("frappe.flow.is_enabled", return_value=value, create=True)

	def test_not_available_when_flow_cannot_chat(self):
		with self.flow_enabled(False):
			self.assertFalse(ask_flow.flow_available())

	def test_only_a_flow_user_sees_flow(self):
		frappe.set_user(AGENT)
		with self.flow_enabled():
			self.assertFalse(ask_flow.flow_available())
			frappe.set_user("Administrator")
			frappe.get_doc("User", AGENT).add_roles(FLOW_ROLE)
			frappe.set_user(AGENT)
			self.assertTrue(ask_flow.flow_available())


class TestFlowRoleOnJoining(IntegrationTestCase):
	def setUp(self):
		if not frappe.db.exists("Role", FLOW_ROLE):
			self.skipTest("Frappe v16 has no Flow")

	def tearDown(self):
		frappe.db.rollback()

	def new_user(self):
		return make_plain_user(f"flow-{frappe.generate_hash(length=6)}@example.com").name

	def test_joining_the_crm_gives_flow(self):
		user = self.new_user()
		update_user_role(user, "Sales User")
		self.assertIn(FLOW_ROLE, user_roles(user))

	def test_a_role_change_does_not_give_flow_back(self):
		user = self.new_user()
		update_user_role(user, "Sales User")
		frappe.get_doc("User", user).remove_roles(FLOW_ROLE)
		update_user_role(user, "Sales Manager")
		self.assertNotIn(FLOW_ROLE, user_roles(user))

	def test_accepting_an_invitation_gives_flow(self):
		email = f"flow-{frappe.generate_hash(length=6)}@example.com"
		with patch.object(frappe, "sendmail"):
			invitation = frappe.get_doc(doctype="CRM Invitation", email=email, role="Sales User").insert(
				ignore_permissions=True
			)
		invitation.accept()
		self.assertIn(FLOW_ROLE, user_roles(email))

	def test_patch_gives_flow_to_sales_users_who_joined_before_it(self):
		user = self.new_user()
		frappe.get_doc("User", user).add_roles("Sales User")
		outsider = self.new_user()
		give_sales_users_flow_role()
		self.assertIn(FLOW_ROLE, user_roles(user))
		self.assertNotIn(FLOW_ROLE, user_roles(outsider))
