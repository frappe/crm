# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from crm.api.whatsapp import (
	_validate_template_for_reference,
	get_sendable_templates,
	get_whatsapp_messages,
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


class TestGetWhatsappMessagesStatusNormalization(FrappeTestCase):
	"""The frontend matches lowercase status values; upstream stores Title Case."""

	def _fake_message(self, status):
		# from=None routes through the "You" branch so get_from_name (which would
		# call frappe.get_doc on the CRM record) is skipped.
		return frappe._dict(
			name="msg1",
			direction="Outgoing",
			to="profile1",
			**{"from": None},
			mime_type=None,
			is_template=0,
			media_url=None,
			whatsapp_template=None,
			message_id="m1",
			context_message_id=None,
			creation=None,
			message="hi",
			status=status,
			reference_doctype="CRM Lead",
			reference_docname="LEAD-0001",
			template_body_parameters=None,
			template_header_parameters=None,
		)

	def _run(self, status):
		reference_doc = MagicMock()
		reference_doc.get.return_value = None
		with (
			patch("crm.api.whatsapp.validate_access", return_value=reference_doc),
			patch("frappe.get_installed_apps", return_value=[]),
			patch("frappe.db.exists", return_value=True),
			patch("frappe.get_all", return_value=[self._fake_message(status)]),
		):
			return get_whatsapp_messages("CRM Lead", "LEAD-0001")

	def test_failed_status_lowercased(self):
		result = self._run("Failed")
		self.assertEqual(result[0]["status"], "failed")

	def test_delivered_status_lowercased(self):
		self.assertEqual(self._run("Delivered")[0]["status"], "delivered")

	def test_already_lowercase_status_unchanged(self):
		self.assertEqual(self._run("sent")[0]["status"], "sent")

	def test_empty_status_becomes_empty_string(self):
		self.assertEqual(self._run(None)[0]["status"], "")


class TestCreateWhatsAppMediaMessage(FrappeTestCase):
	"""Attachments must travel through the Whatsapp app's media-upload path.

	Regression: CRM used to store the file URL in `media_url`/`message` only, so the
	app's send path (which keys off the `attach` File reference) skipped the Meta media
	upload and fell back to sending the file path as a plain text message.
	"""

	def tearDown(self):
		frappe.db.rollback()

	def _make_account(self):
		return (
			frappe.get_doc(
				doctype="Whatsapp Account",
				account_name=f"_Test Acc {frappe.generate_hash(length=6)}",
				status="Active",
				phone_id="1234567890",
				business_id="biz",
				app_id="app",
				access_token="tok",
			)
			.insert(ignore_permissions=True)
			.name
		)

	def test_attachment_sends_as_media_not_text(self):
		from crm.api.whatsapp import create_whatsapp_message

		account = self._make_account()
		setting = frappe.get_single("Whatsapp Setting")
		setting.default_account = account
		setting.save(ignore_permissions=True)

		lead = frappe.get_doc(
			doctype="CRM Lead",
			first_name="Mediatest",
			mobile_no="+15551234567",
		).insert(ignore_permissions=True)

		file_doc = frappe.get_doc(
			doctype="File",
			file_name="pic.png",
			is_private=0,
			content=b"png_bytes",
		).insert(ignore_permissions=True)

		with (
			patch("crm.api.whatsapp.validate_access"),
			patch(
				"whatsapp.whatsapp.api.whatsapp.Whatsapp.upload_media",
				return_value={"id": "media_999"},
			) as mock_upload,
			patch(
				"whatsapp.whatsapp.api.whatsapp.Whatsapp.send_message",
				return_value={"messages": [{"id": "wamid.1"}]},
			) as mock_send,
		):
			name = create_whatsapp_message(
				reference_doctype="CRM Lead",
				reference_name=lead.name,
				message="",
				to=lead.mobile_no,
				attach=file_doc.file_url,
				reply_to="",
				content_type="image",
			)

		msg = frappe.get_doc("Whatsapp Message", name)
		# `attach` must hold the File docname so the upload path runs.
		self.assertEqual(msg.attach, file_doc.name)
		# The file URL must not leak into the text body.
		self.assertNotIn("/files/", msg.message or "")
		# `media_url` is retained for the CRM activity-feed display.
		self.assertEqual(msg.media_url, file_doc.file_url)

		mock_upload.assert_called_once()
		payload = mock_send.call_args[0][0]
		self.assertEqual(payload["type"], "image")
		self.assertEqual(payload["image"]["id"], "media_999")
