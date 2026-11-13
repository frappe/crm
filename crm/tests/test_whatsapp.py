# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import MagicMock, patch

import frappe

from crm.api.whatsapp import notify_agent, on_update, validate
from crm.tests import CRMTestCase as FrappeTestCase


class TestWhatsAppHooks(FrappeTestCase):
	def tearDown(self):
		frappe.db.rollback()

	# --- on_update() ---

	def test_on_update_publishes_to_reference_doc_room(self):
		doc = MagicMock(reference_doctype="CRM Lead", reference_name="LEAD-0001")

		with (
			patch("crm.api.whatsapp.frappe.publish_realtime") as publish,
			patch("crm.api.whatsapp.notify_agent"),
		):
			on_update(doc, None)

		publish.assert_called_once_with(
			"whatsapp_message",
			{"reference_doctype": "CRM Lead", "reference_name": "LEAD-0001"},
			doctype="CRM Lead",
			docname="LEAD-0001",
		)

	def test_on_update_does_not_broadcast_without_reference(self):
		doc = MagicMock(reference_doctype=None, reference_name=None)

		with (
			patch("crm.api.whatsapp.frappe.publish_realtime") as publish,
			patch("crm.api.whatsapp.notify_agent") as notify,
		):
			on_update(doc, None)

		publish.assert_not_called()
		notify.assert_called_once_with(doc)

	# --- validate() ---

	def test_validate_sets_reference_when_contact_found(self):
		"""validate() links the doc when a matching Contact/Lead is found"""
		doc = MagicMock()
		doc.type = "Incoming"
		doc.get.return_value = "+15551234567"

		with patch(
			"crm.api.whatsapp.get_contact_lead_or_deal_from_number",
			return_value=("LEAD-0001", "CRM Lead"),
		):
			validate(doc, None)

		self.assertEqual(doc.reference_doctype, "CRM Lead")
		self.assertEqual(doc.reference_name, "LEAD-0001")

	def test_validate_skips_reference_when_no_contact_found(self):
		"""validate() leaves reference fields untouched when number is unknown"""
		doc = MagicMock()
		doc.type = "Incoming"
		doc.get.return_value = "+15559999999"
		doc.reference_doctype = None
		doc.reference_name = None

		with patch(
			"crm.api.whatsapp.get_contact_lead_or_deal_from_number",
			return_value=(None, None),
		):
			validate(doc, None)

		self.assertIsNone(doc.reference_doctype)
		self.assertIsNone(doc.reference_name)

	def test_validate_logs_error_on_exception(self):
		"""validate() catches lookup exceptions and logs them instead of raising"""
		doc = MagicMock()
		doc.type = "Incoming"
		doc.get.return_value = "invalid-number"

		with (
			patch(
				"crm.api.whatsapp.get_contact_lead_or_deal_from_number",
				side_effect=Exception("parse error"),
			),
			patch("frappe.log_error") as mock_log,
		):
			validate(doc, None)  # must not raise

		mock_log.assert_called_once()

	# --- notify_agent() ---

	def test_notify_agent_returns_early_when_no_reference(self):
		"""notify_agent() skips notification when reference_doctype and reference_name are absent"""
		doc = MagicMock()
		doc.type = "Incoming"
		doc.reference_doctype = None
		doc.reference_name = None

		with patch("crm.api.whatsapp.get_assignees") as mock_users:
			notify_agent(doc)  # must not raise

		mock_users.assert_not_called()

	def test_notify_agent_returns_early_when_reference_doctype_missing(self):
		"""notify_agent() skips notification when only reference_doctype is absent"""
		doc = MagicMock()
		doc.type = "Incoming"
		doc.reference_doctype = ""
		doc.reference_name = "LEAD-0001"

		with patch("crm.api.whatsapp.get_assignees") as mock_users:
			notify_agent(doc)

		mock_users.assert_not_called()

	def test_notify_agent_runs_as_guest_like_the_webhook(self):
		"""notify_agent() notifies the assignees when the Guest webhook user has no read access to the lead"""
		lead = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Webhook"}).insert(
			ignore_permissions=True
		)
		frappe.get_doc(
			{
				"doctype": "ToDo",
				"allocated_to": "Administrator",
				"reference_type": "CRM Lead",
				"reference_name": lead.name,
				"description": "Assigned",
			}
		).insert(ignore_permissions=True)
		doc = frappe._dict(
			name="MSG-1",
			owner="Guest",
			type="Incoming",
			message="Hi",
			reference_doctype="CRM Lead",
			reference_name=lead.name,
		)

		frappe.set_user("Guest")
		try:
			with patch("crm.api.whatsapp.notify_user") as mock_notify:
				notify_agent(doc)
		finally:
			frappe.set_user("Administrator")

		self.assertEqual([c.args[0]["assigned_to"] for c in mock_notify.call_args_list], ["Administrator"])
