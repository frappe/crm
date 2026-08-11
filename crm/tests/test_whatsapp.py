# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from crm.api.whatsapp import (
	ALLOWED_WHATSAPP_ROLES,
	is_whatsapp_enabled,
	notify_agent,
	validate,
	validate_access,
)


class TestWhatsAppHooks(FrappeTestCase):
	def tearDown(self):
		frappe.db.rollback()

	# --- validate() ---

	def test_validate_sets_reference_when_contact_found(self):
		"""validate() links the doc when a matching Contact/Lead is found"""
		doc = MagicMock()
		doc.direction = "Incoming"

		with (
			patch(
				"crm.api.whatsapp._get_phone_number_from_profile",
				return_value="+15551234567",
			),
			patch("crm.api.whatsapp._link_profile_to_crm_entities"),
			patch(
				"crm.api.whatsapp.get_contact_lead_or_deal_from_number",
				return_value=("LEAD-0001", "CRM Lead"),
			),
		):
			validate(doc, None)

		self.assertEqual(doc.reference_doctype, "CRM Lead")
		self.assertEqual(doc.reference_docname, "LEAD-0001")

	def test_validate_skips_reference_when_no_contact_found(self):
		"""validate() leaves reference fields untouched when number is unknown"""
		doc = MagicMock()
		doc.direction = "Incoming"
		doc.reference_doctype = None
		doc.reference_docname = None

		with (
			patch(
				"crm.api.whatsapp._get_phone_number_from_profile",
				return_value="+15559999999",
			),
			patch("crm.api.whatsapp._link_profile_to_crm_entities"),
			patch(
				"crm.api.whatsapp.get_contact_lead_or_deal_from_number",
				return_value=(None, None),
			),
		):
			validate(doc, None)

		self.assertIsNone(doc.reference_doctype)
		self.assertIsNone(doc.reference_docname)

	def test_validate_logs_error_on_exception(self):
		"""validate() catches lookup exceptions and logs them instead of raising"""
		doc = MagicMock()
		doc.direction = "Incoming"

		with (
			patch(
				"crm.api.whatsapp._get_phone_number_from_profile",
				return_value="invalid-number",
			),
			patch("crm.api.whatsapp._link_profile_to_crm_entities"),
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
		"""notify_agent() skips notification when reference_doctype and reference_docname are absent"""
		doc = MagicMock()
		doc.direction = "Incoming"
		doc.reference_doctype = None
		doc.reference_docname = None

		with patch("crm.api.whatsapp.get_assigned_users") as mock_users:
			notify_agent(doc)  # must not raise

		mock_users.assert_not_called()

	def test_notify_agent_returns_early_when_reference_doctype_missing(self):
		"""notify_agent() skips notification when only reference_doctype is absent"""
		doc = MagicMock()
		doc.direction = "Incoming"
		doc.reference_doctype = ""
		doc.reference_docname = "LEAD-0001"

		with patch("crm.api.whatsapp.get_assigned_users") as mock_users:
			notify_agent(doc)

		mock_users.assert_not_called()


class TestIsWhatsAppEnabled(FrappeTestCase):
	def test_disabled_when_twilio_integration_installed(self):
		"""twilio_integration's own "WhatsApp Message" DocType collides, so the tab must not render."""
		with (
			patch("frappe.get_installed_apps", return_value=["frappe", "crm", "twilio_integration"]),
			patch("frappe.db.exists", return_value=True) as mock_exists,
		):
			self.assertFalse(is_whatsapp_enabled())

		mock_exists.assert_not_called()

	def test_disabled_when_settings_doctype_missing(self):
		with (
			patch("frappe.get_installed_apps", return_value=["frappe", "crm"]),
			patch("frappe.db.exists", return_value=False),
		):
			self.assertFalse(is_whatsapp_enabled())

	def test_disabled_when_no_default_account(self):
		with (
			patch("frappe.get_installed_apps", return_value=["frappe", "crm", "whatsapp"]),
			patch("frappe.db.exists", return_value=True),
			patch("frappe.get_cached_value", return_value=None),
		):
			self.assertFalse(is_whatsapp_enabled())

	def test_enabled_when_default_account_is_active(self):
		with (
			patch("frappe.get_installed_apps", return_value=["frappe", "crm", "whatsapp"]),
			patch("frappe.db.exists", return_value=True),
			patch("frappe.get_cached_value", side_effect=["_Test Account", "Active"]),
		):
			self.assertTrue(is_whatsapp_enabled())


class TestValidateAccess(FrappeTestCase):
	"""Registered as the WhatsApp app's `whatsapp_access_guard` hook, so this role check is
	what gates that app's whitelisted endpoints for CRM users."""

	def test_raises_for_user_without_an_allowed_role(self):
		with patch("frappe.get_roles", return_value=["All", "Guest"]):
			with self.assertRaises(frappe.PermissionError):
				validate_access()

	def test_passes_for_each_allowed_role(self):
		for role in ALLOWED_WHATSAPP_ROLES:
			with self.subTest(role=role):
				with patch("frappe.get_roles", return_value=["All", role]):
					self.assertIsNone(validate_access())
