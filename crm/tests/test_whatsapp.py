# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import random
from contextlib import contextmanager
from unittest.mock import MagicMock, call, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from crm.api.whatsapp import (
	ALLOWED_WHATSAPP_ROLES,
	CONFIRM_PARAM,
	LEAD_SOURCE,
	WhatsAppRecipientChangeError,
	_get_phone_number_from_profile,
	_link_profile_to_crm_entities,
	add_roles,
	count_conversation,
	get_account_usage,
	guard_doc_recipient_change,
	guard_recipient_change,
	is_whatsapp_enabled,
	is_whatsapp_installed,
	notify_agent,
	validate,
	validate_access,
)
from crm.patches.v1_0.add_whatsapp_lead_source import execute as add_whatsapp_lead_source

COUNT = "crm.api.whatsapp.count_conversation"
OLD = "+91 98765 43220"
NEW = "+91 98765 43221"


@contextmanager
def confirmed():
	frappe.form_dict[CONFIRM_PARAM] = 1
	try:
		yield
	finally:
		frappe.form_dict.pop(CONFIRM_PARAM, None)


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
			patch("crm.api.whatsapp._lead_append_action", return_value=None),
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

		with patch("crm.api.whatsapp.get_assignees") as mock_users:
			notify_agent(doc)  # must not raise

		mock_users.assert_not_called()

	def test_notify_agent_returns_early_when_reference_doctype_missing(self):
		"""notify_agent() skips notification when only reference_doctype is absent"""
		doc = MagicMock()
		doc.direction = "Incoming"
		doc.reference_doctype = ""
		doc.reference_docname = "LEAD-0001"

		with patch("crm.api.whatsapp.get_assignees") as mock_users:
			notify_agent(doc)

		mock_users.assert_not_called()

	def test_notify_agent_notifies_each_assigned_user(self):
		doc = frappe._dict(
			name="MSG-1",
			owner="Administrator",
			direction="Incoming",
			message="Hi",
			reference_doctype="CRM Lead",
			reference_docname="<b>LEAD-1</b>",
		)

		with (
			patch("crm.api.whatsapp.get_assignees", return_value=["a@example.com", "b@example.com"]),
			patch("crm.api.whatsapp.notify_user") as mock_notify,
		):
			notify_agent(doc)

		self.assertEqual(
			[c.args[0]["assigned_to"] for c in mock_notify.call_args_list], ["a@example.com", "b@example.com"]
		)
		sent = mock_notify.call_args.args[0]
		self.assertEqual(sent["notification_type"], "WhatsApp")
		self.assertEqual(sent["reference_doctype"], "WA Message")
		self.assertEqual(sent["redirect_to_docname"], "<b>LEAD-1</b>")
		self.assertIn("in lead", sent["notification_text"])
		self.assertNotIn("<b>LEAD-1</b>", sent["notification_text"])

	def test_notify_agent_ignores_outgoing_messages(self):
		doc = frappe._dict(direction="Outgoing", reference_doctype="CRM Lead", reference_docname="LEAD-1")

		with patch("crm.api.whatsapp.get_assignees") as mock_users:
			notify_agent(doc)

		mock_users.assert_not_called()

	# --- _get_phone_number_from_profile() ---

	def test_phone_number_is_none_without_a_profile(self):
		self.assertIsNone(_get_phone_number_from_profile(frappe._dict(to=None)))

		with patch("frappe.db.exists", return_value=False):
			self.assertIsNone(_get_phone_number_from_profile(frappe._dict(to="missing")))

	def test_phone_number_comes_from_the_profile(self):
		with (
			patch("frappe.db.exists", return_value=True),
			patch("frappe.db.get_value", return_value=OLD) as mock_get_value,
		):
			self.assertEqual(_get_phone_number_from_profile(frappe._dict(to="PROFILE-1")), OLD)

		mock_get_value.assert_called_once_with("WA Profile", "PROFILE-1", "phone_number")

	# --- _link_profile_to_crm_entities() ---

	def _link_profile(self, profile, matches):
		with (
			patch("frappe.db.exists", return_value=True),
			patch("frappe.db.get_value", return_value=OLD),
			patch("crm.api.whatsapp.find_by_phone", return_value=matches),
			patch("frappe.get_doc", return_value=profile),
		):
			_link_profile_to_crm_entities(frappe._dict(to="PROFILE-1"))

	def test_link_profile_adds_only_missing_links(self):
		profile = MagicMock()
		profile.links = [frappe._dict(link_doctype="CRM Lead", link_name="LEAD-1")]

		self._link_profile(
			profile,
			[{"doctype": "CRM Lead", "docname": "LEAD-1"}, {"doctype": "CRM Deal", "docname": "DEAL-1"}],
		)

		profile.append.assert_called_once_with(
			"links", {"link_doctype": "CRM Deal", "link_name": "DEAL-1", "link_title": "DEAL-1"}
		)
		profile.save.assert_called_once()

	def test_link_profile_does_not_save_when_already_linked(self):
		profile = MagicMock()
		profile.links = [frappe._dict(link_doctype="CRM Lead", link_name="LEAD-1")]

		self._link_profile(profile, [{"doctype": "CRM Lead", "docname": "LEAD-1"}])

		profile.save.assert_not_called()

	def test_link_profile_logs_error_instead_of_raising(self):
		with (
			patch("frappe.db.exists", side_effect=Exception("db down")),
			patch("frappe.log_error") as mock_log,
		):
			_link_profile_to_crm_entities(frappe._dict(to="PROFILE-1"))

		mock_log.assert_called_once()


class TestIsWhatsAppEnabled(FrappeTestCase):
	def test_enabled_alongside_twilio_integration(self):
		with (
			patch(
				"frappe.get_installed_apps", return_value=["frappe", "crm", "whatsapp", "twilio_integration"]
			),
			patch("frappe.db.exists", return_value=True),
			patch("frappe.get_cached_value", side_effect=["_Test Account", "Active"]),
		):
			self.assertTrue(is_whatsapp_enabled())

	def test_disabled_when_settings_doctype_missing(self):
		with patch("frappe.db.exists", return_value=False):
			self.assertFalse(is_whatsapp_enabled())

	def test_disabled_when_no_default_account(self):
		with (
			patch("frappe.db.exists", return_value=True),
			patch("frappe.get_cached_value", return_value=None),
		):
			self.assertFalse(is_whatsapp_enabled())

	def test_enabled_when_default_account_is_active(self):
		with (
			patch("frappe.db.exists", return_value=True),
			patch("frappe.get_cached_value", side_effect=["_Test Account", "Active"]),
		):
			self.assertTrue(is_whatsapp_enabled())


class TestIsWhatsAppInstalled(FrappeTestCase):
	def test_installed_when_settings_doctype_exists(self):
		with patch("frappe.db.exists", return_value=True):
			self.assertTrue(is_whatsapp_installed())

	def test_not_installed_without_settings_doctype(self):
		with patch("frappe.db.exists", return_value=False):
			self.assertFalse(is_whatsapp_installed())


class TestAddRoles(FrappeTestCase):
	def test_skipped_when_whatsapp_is_not_installed(self):
		with (
			patch("frappe.get_installed_apps", return_value=["frappe", "crm"]),
			patch("crm.api.whatsapp.add_permission") as mock_add,
		):
			add_roles()

		mock_add.assert_not_called()

	def test_adds_permissions_only_for_roles_without_them(self):
		with (
			patch("frappe.get_installed_apps", return_value=["frappe", "crm", "whatsapp"]),
			patch("frappe.db.exists", side_effect=lambda _doctype, filters: filters["role"] == "Sales User"),
			patch("crm.api.whatsapp.add_permission") as mock_add,
			patch("crm.api.whatsapp.update_permission_property"),
		):
			add_roles()

		self.assertEqual(
			mock_add.call_args_list,
			[
				call(doctype, "Sales Manager", 0, "write")
				for doctype in ("WA Message", "WA Template", "WA Settings", "WA Profile")
			],
		)


class TestGetAccountUsage(FrappeTestCase):
	"""Counts what still links to an account, so the UI can explain a refused delete
	rather than surfacing Frappe's link-exists error."""

	def test_counts_each_linked_doctype(self):
		with (
			patch("frappe.get_roles", return_value=["System Manager"]),
			patch("frappe.db.exists", return_value=True),
			patch("frappe.db.count", side_effect=[12, 3, 0, 5]),
		):
			usage = get_account_usage("_Test Account")

		self.assertEqual(
			usage,
			{
				"WA Message": 12,
				"WA Profile": 3,
				"WA Template": 0,
				"WA Log": 5,
			},
		)

	def test_skips_doctypes_that_are_not_installed(self):
		with (
			patch("frappe.get_roles", return_value=["System Manager"]),
			patch("frappe.db.exists", side_effect=[True, True, False, False]),
			patch("frappe.db.count", return_value=0),
		):
			usage = get_account_usage("_Test Account")

		self.assertEqual(set(usage), {"WA Message", "WA Profile"})

	def test_raises_for_user_without_an_allowed_role(self):
		with patch("frappe.get_roles", return_value=["All", "Guest"]):
			with self.assertRaises(frappe.PermissionError):
				get_account_usage("_Test Account")


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


class TestGuardRecipientChange(FrappeTestCase):
	def test_record_without_a_number_is_allowed(self):
		with patch(COUNT) as count:
			guard_recipient_change("CRM Lead", "LEAD-1", None, NEW)
		count.assert_not_called()

	def test_same_number_in_another_format_is_allowed(self):
		with patch(COUNT) as count:
			guard_recipient_change("CRM Lead", "LEAD-1", OLD, "919876543220")
		count.assert_not_called()

	def test_number_without_a_conversation_is_allowed(self):
		with patch(COUNT, return_value=0):
			guard_recipient_change("CRM Lead", "LEAD-1", OLD, NEW)

	def test_moving_off_a_number_with_a_conversation_is_refused(self):
		with patch(COUNT, return_value=3), self.assertRaises(WhatsAppRecipientChangeError) as refused:
			guard_recipient_change("CRM Deal", "DEAL-1", OLD, NEW)

		message = str(refused.exception)
		self.assertIn(OLD, message)
		self.assertIn(NEW, message)
		self.assertIn("3", message)

	def test_clearing_the_number_says_they_can_no_longer_be_messaged(self):
		with patch(COUNT, return_value=1), self.assertRaises(WhatsAppRecipientChangeError) as refused:
			guard_recipient_change("CRM Lead", "LEAD-1", OLD, "")

		self.assertIn("won't be able to message them", str(refused.exception))

	def test_confirmed_request_is_allowed(self):
		with patch(COUNT, return_value=3), confirmed():
			guard_recipient_change("CRM Lead", "LEAD-1", OLD, NEW)

	def test_data_import_is_not_blocked(self):
		with patch(COUNT, return_value=3), patch.dict(frappe.flags, {"in_import": True}):
			guard_recipient_change("CRM Lead", "LEAD-1", OLD, NEW)


class TestRecipientChangePaths(FrappeTestCase):
	"""Every path that moves a Lead or Deal off its number has to go through the guard."""

	def _contact(self, mobile_no: str):
		contact = frappe.get_doc(
			{"doctype": "Contact", "first_name": "Recipient", "last_name": frappe.generate_hash(length=5)}
		)
		contact.append("phone_nos", {"phone": mobile_no, "is_primary_mobile_no": 1})
		return contact.insert()

	def _deal(self, *contacts):
		org = frappe.get_doc(
			{"doctype": "CRM Organization", "organization_name": frappe.generate_hash(length=6)}
		).insert()
		deal = frappe.get_doc(
			{"doctype": "CRM Deal", "organization": org.name, "deal_owner": "Administrator"}
		)
		for index, contact in enumerate(contacts):
			deal.append("contacts", {"contact": contact.name, "is_primary": int(index == 0)})
		return deal.insert()

	def test_lead_number_change(self):
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Recipient",
				"mobile_no": OLD,
				"lead_owner": "Administrator",
			}
		).insert()

		with patch(COUNT, return_value=2):
			lead.mobile_no = NEW
			self.assertRaises(WhatsAppRecipientChangeError, lead.save)

			lead.reload()
			lead.mobile_no = NEW
			with confirmed():
				lead.save()

		self.assertEqual(frappe.db.get_value("CRM Lead", lead.name, "mobile_no"), NEW)

	def test_removing_the_deal_contact(self):
		from crm.fcrm.doctype.crm_deal.crm_deal import remove_contact

		contact = self._contact(OLD)
		deal = self._deal(contact)

		with patch(COUNT, return_value=2):
			self.assertRaises(WhatsAppRecipientChangeError, remove_contact, deal.name, contact.name)
			frappe.clear_document_cache("CRM Deal", deal.name)
			with confirmed():
				remove_contact(deal.name, contact.name)

		self.assertFalse(frappe.db.get_value("CRM Deal", deal.name, "mobile_no"))

	def test_last_other_contact_taking_over_as_primary(self):
		from crm.fcrm.doctype.crm_deal.crm_deal import remove_contact

		first, second = self._contact(OLD), self._contact(NEW)
		deal = self._deal(first, second)

		with patch(COUNT, return_value=2), self.assertRaises(WhatsAppRecipientChangeError) as refused:
			remove_contact(deal.name, first.name)

		self.assertIn(NEW, str(refused.exception))

	def test_contact_number_change_carried_to_its_deal(self):
		contact = self._contact(OLD)
		deal = self._deal(contact)

		contact.reload()
		contact.phone_nos[0].phone = NEW
		with patch(COUNT, return_value=2):
			self.assertRaises(WhatsAppRecipientChangeError, contact.save)

			contact.reload()
			contact.phone_nos[0].phone = NEW
			with confirmed():
				contact.save()

		self.assertEqual(frappe.db.get_value("CRM Deal", deal.name, "mobile_no"), NEW)
		version = frappe.get_last_doc("Version", filters={"ref_doctype": "CRM Deal", "docname": deal.name})
		self.assertIn(["mobile_no", OLD, NEW], frappe.parse_json(version.data)["changed"])

	def test_unlinking_a_contact_is_not_silently_skipped(self):
		from crm.api.doc import remove_linked_doc_reference

		contact = self._contact(OLD)
		deal = self._deal(contact)

		with patch(COUNT, return_value=2):
			self.assertRaises(
				WhatsAppRecipientChangeError,
				remove_linked_doc_reference,
				[{"doctype": "CRM Deal", "docname": deal.name}],
				remove_contact=True,
			)


class TestGuardDocRecipientChange(FrappeTestCase):
	def _doc(self, before):
		doc = MagicMock(doctype="CRM Lead", mobile_no=NEW)
		doc.name = "LEAD-1"
		doc.is_new.return_value = before is None
		doc.get_doc_before_save.return_value = before
		return doc

	def test_new_record_is_not_checked(self):
		with patch("crm.api.whatsapp.guard_recipient_change") as guard:
			guard_doc_recipient_change(self._doc(None))

		guard.assert_not_called()

	def test_saved_record_is_checked_against_its_previous_number(self):
		with patch("crm.api.whatsapp.guard_recipient_change") as guard:
			guard_doc_recipient_change(self._doc(frappe._dict(mobile_no=OLD)))

		guard.assert_called_once_with("CRM Lead", "LEAD-1", OLD, NEW)


class TestCountConversation(FrappeTestCase):
	def _profile(self, phone_number: str) -> str:
		profile = frappe.get_doc(
			{"doctype": "WA Profile", "name": frappe.generate_hash(length=10), "phone_number": phone_number}
		)
		profile.db_insert()
		return profile.name

	def _messages(self, count: int, to: str, doctype: str, docname: str):
		for _ in range(count):
			frappe.get_doc(
				{
					"doctype": "WA Message",
					"name": frappe.generate_hash(length=10),
					"to": to,
					"reference_doctype": doctype,
					"reference_docname": docname,
				}
			).db_insert()

	def setUp(self):
		self.lead = f"LEAD-{frappe.generate_hash(length=6)}"
		self.deal = f"DEAL-{frappe.generate_hash(length=6)}"
		old = self._profile(OLD)
		old_other_format = self._profile("919876543220")
		self._messages(2, old, "CRM Lead", self.lead)
		self._messages(1, old_other_format, "CRM Lead", self.lead)
		self._messages(4, self._profile(NEW), "CRM Lead", self.lead)
		self._messages(1, old, "CRM Deal", self.deal)

	def test_counts_the_number_in_any_format(self):
		self.assertEqual(count_conversation("CRM Lead", self.lead, OLD), 3)

	def test_deal_includes_the_messages_of_its_lead(self):
		with patch("frappe.db.get_value", return_value=self.lead):
			self.assertEqual(count_conversation("CRM Deal", self.deal, OLD), 4)

	def test_no_number_counts_nothing(self):
		self.assertEqual(count_conversation("CRM Lead", self.lead, ""), 0)


class TestLeadFromIncomingWhatsApp(FrappeTestCase):
	"""An account that appends incoming messages to CRM Lead gets a Lead for each new sender,
	stamped with the WhatsApp source, before the whatsapp app's own append action runs."""

	def setUp(self):
		add_whatsapp_lead_source()
		self.number = f"+9198765{random.randint(10000, 99999)}"

	def tearDown(self):
		frappe.db.rollback()

	def _message(self, append_actions=None, direction="Incoming", profile_name="Asha"):
		account = frappe.get_doc(
			{
				"doctype": "WA Account",
				"account_name": f"_Test Lead Source {frappe.generate_hash(length=5)}",
				"status": "Active",
				"phone_id": frappe.generate_hash(length=8),
				"append_actions": append_actions or [],
			}
		).insert()
		profile = frappe.get_doc(
			{
				"doctype": "WA Profile",
				"whatsapp_account": account.name,
				"phone_number": self.number,
				"profile_name": profile_name,
			}
		).insert()
		return frappe.get_doc(
			{
				"doctype": "WA Message",
				"direction": direction,
				"whatsapp_account": account.name,
				"to": profile.name,
				"message": "Hi, tell me more",
			}
		)

	def _lead_action(self, trigger_on="Incoming", **mapping):
		return {
			"append_to": "CRM Lead",
			"trigger_on": trigger_on,
			"sender_field": "mobile_no",
			"sender_name_field": "first_name",
			**mapping,
		}

	def _leads(self):
		return frappe.get_all("CRM Lead", filters={"mobile_no": self.number}, pluck="name")

	def test_unknown_sender_becomes_a_lead_with_the_whatsapp_source(self):
		doc = self._message([self._lead_action(message_field="company_description")])

		validate(doc, None)

		lead = frappe.get_doc("CRM Lead", doc.reference_docname)
		self.assertEqual(doc.reference_doctype, "CRM Lead")
		self.assertEqual(lead.source, LEAD_SOURCE)
		self.assertEqual(lead.mobile_no, self.number)
		self.assertEqual(lead.first_name, "Asha")
		self.assertEqual(lead.company_description, "Hi, tell me more")

	def test_account_without_a_lead_append_action_leaves_the_message_unlinked(self):
		doc = self._message()

		validate(doc, None)

		self.assertFalse(doc.reference_docname)
		self.assertEqual(self._leads(), [])

	def test_outgoing_only_action_does_not_count(self):
		doc = self._message([self._lead_action(trigger_on="Outgoing")])

		validate(doc, None)

		self.assertEqual(self._leads(), [])

	def test_outgoing_message_never_creates_a_lead(self):
		doc = self._message([self._lead_action()], direction="Outgoing")

		validate(doc, None)

		self.assertEqual(self._leads(), [])

	def test_known_number_is_linked_instead_of_duplicated(self):
		existing = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Known", "mobile_no": self.number}
		).insert()
		doc = self._message([self._lead_action()])

		validate(doc, None)

		self.assertEqual(doc.reference_docname, existing.name)
		self.assertEqual(self._leads(), [existing.name])
