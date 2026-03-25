# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from crm.api.whatsapp import notify_agent, validate


class TestWhatsAppHooks(FrappeTestCase):
	def tearDown(self):
		frappe.db.rollback()

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

		with patch("crm.api.whatsapp.get_assigned_users") as mock_users:
			notify_agent(doc)  # must not raise

		mock_users.assert_not_called()

	def test_notify_agent_returns_early_when_reference_doctype_missing(self):
		"""notify_agent() skips notification when only reference_doctype is absent"""
		doc = MagicMock()
		doc.type = "Incoming"
		doc.reference_doctype = ""
		doc.reference_name = "LEAD-0001"

		with patch("crm.api.whatsapp.get_assigned_users") as mock_users:
			notify_agent(doc)

		mock_users.assert_not_called()
