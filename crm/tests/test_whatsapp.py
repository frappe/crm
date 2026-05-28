# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from crm.api.whatsapp import (
	_validate_template_for_reference,
	get_sendable_templates,
	notify_agent,
	parse_template_parameters,
	validate,
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


class TestValidateTemplateForReference(FrappeTestCase):
	def _patch_template(self, **fields):
		"""Stub frappe.db.exists + frappe.get_cached_doc for a Whatsapp Template."""
		template = MagicMock()
		template.get.side_effect = lambda key, default=None: fields.get(key, default)
		return patch("frappe.db.exists", return_value=True), patch(
			"frappe.get_cached_doc", return_value=template
		)

	def test_raises_when_template_does_not_exist(self):
		with patch("frappe.db.exists", return_value=False):
			with self.assertRaises(frappe.DoesNotExistError):
				_validate_template_for_reference("missing_template", "CRM Lead")

	def test_passes_when_template_has_no_variables(self):
		exists, get_doc = self._patch_template(template_variables=[], reference_doctype="")
		with exists, get_doc:
			_validate_template_for_reference("plain_template", "CRM Deal")  # must not raise

	def test_raises_when_template_has_vars_but_no_reference_doctype(self):
		exists, get_doc = self._patch_template(template_variables=[MagicMock()], reference_doctype="")
		with exists, get_doc:
			with self.assertRaises(frappe.ValidationError) as ctx:
				_validate_template_for_reference("orphan_template", "CRM Lead")
			self.assertIn("not bound to a reference DocType", str(ctx.exception))

	def test_raises_when_template_doctype_mismatches(self):
		exists, get_doc = self._patch_template(template_variables=[MagicMock()], reference_doctype="CRM Lead")
		with exists, get_doc:
			with self.assertRaises(frappe.ValidationError) as ctx:
				_validate_template_for_reference("lead_template", "CRM Deal")
			self.assertIn("CRM Lead", str(ctx.exception))
			self.assertIn("CRM Deal", str(ctx.exception))

	def test_passes_when_template_doctype_matches(self):
		exists, get_doc = self._patch_template(template_variables=[MagicMock()], reference_doctype="CRM Lead")
		with exists, get_doc:
			_validate_template_for_reference("lead_template", "CRM Lead")  # must not raise

	def test_raises_when_variable_field_is_unmapped(self):
		"""A Template Variable row without a variable_field cannot resolve at send time."""
		unmapped_var = MagicMock()
		unmapped_var.variable_name = "first_name"
		unmapped_var.variable_field = ""
		exists, get_doc = self._patch_template(
			template_variables=[unmapped_var], reference_doctype="CRM Lead"
		)
		with exists, get_doc:
			with self.assertRaises(frappe.ValidationError) as ctx:
				_validate_template_for_reference("lead_template", "CRM Lead")
			self.assertIn("first_name", str(ctx.exception))
			self.assertIn("Variable Field", str(ctx.exception))

	def test_lists_all_unmapped_variables(self):
		v1 = MagicMock()
		v1.variable_name = "first_name"
		v1.variable_field = ""
		v2 = MagicMock()
		v2.variable_name = "amount"
		v2.variable_field = "amount"  # mapped
		v3 = MagicMock()
		v3.variable_name = "last_name"
		v3.variable_field = ""
		exists, get_doc = self._patch_template(template_variables=[v1, v2, v3], reference_doctype="CRM Lead")
		with exists, get_doc:
			with self.assertRaises(frappe.ValidationError) as ctx:
				_validate_template_for_reference("lead_template", "CRM Lead")
			msg = str(ctx.exception)
			self.assertIn("first_name", msg)
			self.assertIn("last_name", msg)
			self.assertNotIn("amount", msg)


class TestGetSendableTemplates(FrappeTestCase):
	def _frappe_dict(self, **kw):
		return frappe._dict(kw)

	def test_returns_empty_when_doctype_missing(self):
		with patch("crm.api.whatsapp.validate_access"), patch("frappe.db.exists", return_value=False):
			self.assertEqual(get_sendable_templates("CRM Lead"), [])

	def test_excludes_unbound_templates_with_variables(self):
		"""Unbound + has vars → cannot resolve, must be hidden."""
		templates = [
			self._frappe_dict(
				name="t_bound",
				reference_doctype="CRM Lead",
				message="m",
				footer="",
				header_text="",
				header_type="TEXT",
			),
			self._frappe_dict(
				name="t_unbound_clean",
				reference_doctype="",
				message="m",
				footer="",
				header_text="",
				header_type="TEXT",
			),
			self._frappe_dict(
				name="t_unbound_vars",
				reference_doctype="",
				message="Hi {{x}}",
				footer="",
				header_text="",
				header_type="TEXT",
			),
		]

		def _get_all(doctype, **kwargs):
			if doctype == "Whatsapp Template":
				return templates
			if doctype == "Template Variable":
				return [self._frappe_dict(parent="t_unbound_vars")]
			return []

		with (
			patch("crm.api.whatsapp.validate_access"),
			patch("frappe.db.exists", return_value=True),
			patch("frappe.get_all", side_effect=_get_all),
		):
			result = get_sendable_templates("CRM Lead")

		names = [t.name for t in result]
		self.assertIn("t_bound", names)
		self.assertIn("t_unbound_clean", names)
		self.assertNotIn("t_unbound_vars", names)

	def test_skips_variable_query_when_no_unbound_templates(self):
		templates = [
			self._frappe_dict(
				name="t_bound",
				reference_doctype="CRM Lead",
				message="m",
				footer="",
				header_text="",
				header_type="TEXT",
			),
		]
		calls = []

		def _get_all(doctype, **kwargs):
			calls.append(doctype)
			if doctype == "Whatsapp Template":
				return templates
			return []

		with (
			patch("crm.api.whatsapp.validate_access"),
			patch("frappe.db.exists", return_value=True),
			patch("frappe.get_all", side_effect=_get_all),
		):
			get_sendable_templates("CRM Lead")

		self.assertNotIn("Template Variable", calls)
