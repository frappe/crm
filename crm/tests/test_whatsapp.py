# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from crm.api.whatsapp import notify_agent, parse_template_parameters, validate


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


class TestParseTemplateParameters(FrappeTestCase):
	# --- dict (named) ---

	def test_dict_substitutes_named_placeholders(self):
		result = parse_template_parameters(
			"Hi {{first_name}}, your deal {{deal_name}} is ready",
			{"first_name": "John", "deal_name": "ACME-001"},
		)
		self.assertEqual(result, "Hi John, your deal ACME-001 is ready")

	def test_dict_handles_whitespace_inside_placeholders(self):
		result = parse_template_parameters("Hi {{ first_name }}", {"first_name": "John"})
		self.assertEqual(result, "Hi John")

	def test_dict_with_numeric_string_keys_acts_positional(self):
		"""Synced positional templates store params as a dict keyed by '1', '2', …"""
		result = parse_template_parameters("Hi {{1}}, your code is {{2}}", {"1": "John", "2": "ABC"})
		self.assertEqual(result, "Hi John, your code is ABC")

	def test_dict_leaves_unknown_placeholders_intact(self):
		result = parse_template_parameters("Hi {{first_name}} {{unknown}}", {"first_name": "John"})
		self.assertEqual(result, "Hi John {{unknown}}")

	def test_dict_coerces_non_string_values(self):
		result = parse_template_parameters("Amount: {{amount}}", {"amount": 5000})
		self.assertEqual(result, "Amount: 5000")

	# --- list (positional) ---

	def test_list_substitutes_by_index(self):
		result = parse_template_parameters("Hi {{1}}, code {{2}}", ["John", "ABC"])
		self.assertEqual(result, "Hi John, code ABC")

	def test_list_ignores_named_placeholders(self):
		result = parse_template_parameters("Hi {{first_name}}", ["John"])
		self.assertEqual(result, "Hi {{first_name}}")

	def test_list_out_of_range_left_intact(self):
		result = parse_template_parameters("{{1}} {{3}}", ["John", "Doe"])
		self.assertEqual(result, "John {{3}}")

	# --- scalar (header storage) ---

	def test_scalar_substitutes_first_placeholder(self):
		result = parse_template_parameters("Welcome {{first_name}}!", "John")
		self.assertEqual(result, "Welcome John!")

	def test_scalar_only_replaces_first_when_multiple_placeholders(self):
		result = parse_template_parameters("{{a}} and {{b}}", "X")
		self.assertEqual(result, "X and {{b}}")

	def test_scalar_int_value(self):
		result = parse_template_parameters("Count: {{n}}", 42)
		self.assertEqual(result, "Count: 42")

	# --- edge cases ---

	def test_empty_string_returns_empty(self):
		self.assertEqual(parse_template_parameters("", {"x": "y"}), "")

	def test_none_parameters_returns_string_unchanged(self):
		self.assertEqual(parse_template_parameters("Hi {{x}}", None), "Hi {{x}}")

	def test_no_placeholders_returns_string_unchanged(self):
		self.assertEqual(parse_template_parameters("No vars here", {"x": "y"}), "No vars here")
