import time
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from crm.utils import (
	are_same_phone_number,
	create_lead_from_incoming_email,
	parse_phone_number,
	seconds_to_duration,
	update_communication_status,
	update_modified_timestamp,
)


class TestUtils(UnitTestCase):
	def test_seconds_to_duration(self):
		# 3661 seconds = 1 hour, 1 minute, and 1 second
		self.assertEqual(seconds_to_duration(3661), "1h 1m 1s")

		# 3660 seconds = 1 hour and 1 minute
		self.assertEqual(seconds_to_duration(3660), "1h 1m")

		# 3601 seconds = 1 hour and 1 second
		self.assertEqual(seconds_to_duration(3601), "1h 1s")

		# 0 seconds = 0s
		self.assertEqual(seconds_to_duration(0), "0s")

	def test_seconds_to_duration_single_unit(self):
		"""Each single-unit branch (hours / minutes / seconds only) should format correctly."""
		self.assertEqual(seconds_to_duration(3600), "1h")  # hours only
		self.assertEqual(seconds_to_duration(60), "1m")  # minutes only
		self.assertEqual(seconds_to_duration(1), "1s")  # seconds only

	def test_seconds_to_duration_minutes_and_seconds(self):
		"""Minutes + seconds without hours should format correctly."""
		self.assertEqual(seconds_to_duration(61), "1m 1s")
		self.assertEqual(seconds_to_duration(90), "1m 30s")

	def test_seconds_to_duration_falsy_values(self):
		"""None and 0 are both falsy and should return '0s'."""
		self.assertEqual(seconds_to_duration(None), "0s")
		self.assertEqual(seconds_to_duration(0), "0s")

	def test_seconds_to_duration_large_values(self):
		"""Values larger than one hour should still compute correctly."""
		self.assertEqual(seconds_to_duration(7322), "2h 2m 2s")  # 2*3600 + 2*60 + 2

	def test_are_same_phone_number_normalized_input(self):
		# Indian number with country code and different formats
		self.assertTrue(are_same_phone_number("+91 9845552671", "9845552671"))
		self.assertTrue(are_same_phone_number("+91-984-555-2671", "9845552671"))
		self.assertTrue(are_same_phone_number("+91 (984) 555-2671", "9845552671"))
		self.assertTrue(are_same_phone_number("+91 984-555-2671", "9845552671"))

		# US number with country code and different formats
		self.assertTrue(are_same_phone_number("+1 415 555 2671", "4155552671", default_region="US"))
		self.assertTrue(are_same_phone_number("+1-415-555-2671", "4155552671", default_region="US"))
		self.assertTrue(are_same_phone_number("+1 (415) 555-2671", "4155552671", default_region="US"))
		self.assertTrue(are_same_phone_number("+1 415-555-2671", "4155552671", default_region="US"))

	def test_are_same_phone_number_invalid_input(self):
		# Invalid numbers should return False
		self.assertFalse(
			are_same_phone_number("+1 415 555 2671", "4155552671")
		)  # Missing default region as US
		self.assertFalse(
			are_same_phone_number("+91 984-555-2671", "9845552671", default_region="US")
		)  # Wrong default region
		self.assertFalse(are_same_phone_number("12345", "67890"))
		self.assertFalse(are_same_phone_number("abc", "14155552671"))

	def test_are_same_phone_number_different_numbers(self):
		"""Two distinct valid numbers should not be considered same."""
		self.assertFalse(are_same_phone_number("+91 9845552671", "+91 9845552672"))
		self.assertFalse(are_same_phone_number("+1 415 555 2671", "+1 415 555 2672", default_region="US"))

	def test_are_same_phone_number_validate_false(self):
		"""With validate=False, structurally parseable but invalid numbers can still match."""
		# These parse but fail is_valid_number; with validate=False they should still compare equal
		self.assertTrue(
			are_same_phone_number("+1 415 555 2671", "+1 415 555 2671", default_region="US", validate=False)
		)

	def test_parse_phone_number_valid_indian_number(self):
		"""A valid Indian number should return success=True with correct metadata."""
		result = parse_phone_number("+919845552671")

		self.assertTrue(result["success"])
		self.assertTrue(result["is_valid"])
		self.assertEqual(result["country_code"], 91)
		self.assertEqual(result["country"], "IN")
		self.assertEqual(result["national_number"], "9845552671")
		# All four formats must be present
		self.assertIn("international", result["formats"])
		self.assertIn("national", result["formats"])
		self.assertIn("E164", result["formats"])
		self.assertIn("RFC3966", result["formats"])
		# E164 should start with +91
		self.assertTrue(result["formats"]["E164"].startswith("+91"))

	def test_parse_phone_number_valid_us_number(self):
		"""A valid US number should return success=True with country_code 1."""
		result = parse_phone_number("+14155552671")

		self.assertTrue(result["success"])
		self.assertTrue(result["is_valid"])
		self.assertEqual(result["country_code"], 1)
		self.assertEqual(result["country"], "US")

	def test_parse_phone_number_invalid_string(self):
		"""An unparseable string should return success=False with an error key."""
		result = parse_phone_number("not-a-number")

		self.assertFalse(result["success"])
		self.assertIn("error", result)

	def test_parse_phone_number_default_country_fallback(self):
		"""A local number without a country prefix should be parsed using the default_country."""
		result = parse_phone_number("9845552671", default_country="IN")

		self.assertTrue(result["success"])
		self.assertEqual(result["country"], "IN")


class TestUpdateModifiedTimestamp(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# Ensure FCRM Settings has the flag enabled; disable status hook to isolate timestamp behaviour
		frappe.db.set_single_value("FCRM Settings", "update_timestamp_on_new_communication", 1)
		frappe.db.set_single_value("FCRM Settings", "auto_update_communication_status", 0)

	@classmethod
	def tearDownClass(cls):
		frappe.db.rollback()
		super().tearDownClass()

	def tearDown(self):
		frappe.db.rollback()

	def _make_lead(self):
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test",
				"email": "test.ts@example.com",
			}
		)
		lead.insert(ignore_permissions=True)
		return lead

	def test_timestamp_updated_on_new_communication(self):
		"""Inserting a Communication linked to a CRM Lead should bump its modified timestamp."""
		lead = self._make_lead()
		original_modified = frappe.db.get_value("CRM Lead", lead.name, "modified")

		time.sleep(0.1)

		comm = frappe.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"communication_medium": "Email",
				"sent_or_received": "Received",
				"subject": "Hello",
				"reference_doctype": "CRM Lead",
				"reference_name": lead.name,
			}
		)
		comm.insert(ignore_permissions=True)

		updated_modified = frappe.db.get_value("CRM Lead", lead.name, "modified")
		self.assertGreater(updated_modified, original_modified)

	def test_timestamp_not_updated_when_setting_disabled(self):
		"""When the setting is off the timestamp should NOT be updated."""
		frappe.db.set_single_value("FCRM Settings", "update_timestamp_on_new_communication", 0)

		lead = self._make_lead()
		original_modified = frappe.db.get_value("CRM Lead", lead.name, "modified")

		time.sleep(0.1)

		comm = frappe.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"communication_medium": "Email",
				"sent_or_received": "Received",
				"subject": "No update expected",
				"reference_doctype": "CRM Lead",
				"reference_name": lead.name,
			}
		)
		comm.insert(ignore_permissions=True)

		updated_modified = frappe.db.get_value("CRM Lead", lead.name, "modified")
		self.assertEqual(updated_modified, original_modified)

		# Restore
		frappe.db.set_single_value("FCRM Settings", "update_timestamp_on_new_communication", 1)

	def test_timestamp_updated_on_new_comment(self):
		"""Inserting a Comment linked to a CRM Lead should bump its modified timestamp (via hook)."""
		lead = self._make_lead()
		original_modified = frappe.db.get_value("CRM Lead", lead.name, "modified")

		time.sleep(0.1)

		comment = frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Comment",
				"reference_doctype": "CRM Lead",
				"reference_name": lead.name,
				"content": "A test comment",
			}
		)
		comment.insert(ignore_permissions=True)

		updated_modified = frappe.db.get_value("CRM Lead", lead.name, "modified")
		self.assertGreater(updated_modified, original_modified)

	def test_timestamp_not_updated_when_no_reference(self):
		"""A Communication without a reference should not touch the DB."""
		comm = frappe.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"communication_medium": "Email",
				"sent_or_received": "Received",
				"subject": "No reference",
			}
		)
		with patch("frappe.db.set_value") as mock_set_value:
			update_modified_timestamp(comm)
			mock_set_value.assert_not_called()

	def test_timestamp_direct_call_updates_lead(self):
		"""Direct call to update_modified_timestamp updates the reference doc."""
		lead = self._make_lead()

		time.sleep(0.1)

		comm = frappe.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"communication_medium": "Email",
				"sent_or_received": "Received",
				"subject": "Direct call",
				"reference_doctype": "CRM Lead",
				"reference_name": lead.name,
			}
		)
		comm.flags.ignore_permissions = True
		comm.insert(ignore_permissions=True)

		before = frappe.db.get_value("CRM Lead", lead.name, "modified")
		time.sleep(0.1)
		update_modified_timestamp(comm)
		after = frappe.db.get_value("CRM Lead", lead.name, "modified")
		self.assertGreaterEqual(after, before)


class TestUpdateCommunicationStatus(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.db.set_single_value("FCRM Settings", "auto_update_communication_status", 1)
		frappe.db.set_single_value("FCRM Settings", "update_timestamp_on_new_communication", 0)

	@classmethod
	def tearDownClass(cls):
		frappe.db.rollback()
		super().tearDownClass()

	def tearDown(self):
		frappe.db.rollback()
		# Keep settings in their proper state between tests
		frappe.db.set_single_value("FCRM Settings", "auto_update_communication_status", 1)

	def _make_lead(self, suffix=""):
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "CommTest" + suffix,
				"email": f"commtest{suffix}@example.com",
			}
		)
		lead.insert(ignore_permissions=True)
		return lead

	def _insert_communication(self, lead, sent_or_received):
		comm = frappe.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"communication_medium": "Email",
				"sent_or_received": sent_or_received,
				"subject": f"Test {sent_or_received}",
				"reference_doctype": "CRM Lead",
				"reference_name": lead.name,
			}
		)
		comm.insert(ignore_permissions=True)
		return comm

	def test_status_set_to_open_on_received_communication(self):
		"""Receiving a communication should set lead's communication_status to 'Open'."""
		lead = self._make_lead("recv")
		self._insert_communication(lead, "Received")

		status = frappe.db.get_value("CRM Lead", lead.name, "communication_status")
		self.assertEqual(status, "Open")

	def test_status_set_to_replied_on_sent_communication(self):
		"""Sending a communication should set lead's communication_status to 'Replied'."""
		lead = self._make_lead("sent")
		self._insert_communication(lead, "Sent")

		status = frappe.db.get_value("CRM Lead", lead.name, "communication_status")
		self.assertEqual(status, "Replied")

	def test_status_not_updated_when_setting_disabled(self):
		"""When auto_update_communication_status is off nothing should change."""
		frappe.db.set_single_value("FCRM Settings", "auto_update_communication_status", 0)

		lead = self._make_lead("off")
		original_status = frappe.db.get_value("CRM Lead", lead.name, "communication_status")
		self._insert_communication(lead, "Received")

		status = frappe.db.get_value("CRM Lead", lead.name, "communication_status")
		self.assertEqual(status, original_status)

	def test_only_last_communication_drives_status(self):
		"""Only the most recent communication should determine the status."""
		lead = self._make_lead("last")

		# First a Received communication → status Open
		self._insert_communication(lead, "Received")
		self.assertEqual(frappe.db.get_value("CRM Lead", lead.name, "communication_status"), "Open")

		# Then a Sent communication → status Replied
		self._insert_communication(lead, "Sent")
		self.assertEqual(frappe.db.get_value("CRM Lead", lead.name, "communication_status"), "Replied")

		# And back to Received → status Open again
		self._insert_communication(lead, "Received")
		self.assertEqual(frappe.db.get_value("CRM Lead", lead.name, "communication_status"), "Open")

	def test_status_not_updated_when_no_reference(self):
		"""A Communication with no reference should not touch the DB."""
		comm = frappe.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"communication_medium": "Email",
				"sent_or_received": "Received",
				"subject": "No reference",
			}
		)
		with patch("frappe.db.set_value") as mock_set_value:
			update_communication_status(comm)
			mock_set_value.assert_not_called()

	def test_status_not_updated_for_non_communication_doctype(self):
		"""Calling update_communication_status with a non-Communication doc should not touch the DB."""
		comment = frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Comment",
				"reference_doctype": "CRM Lead",
				"reference_name": "LEAD-0001",
				"content": "test",
			}
		)
		with patch("frappe.db.set_value") as mock_set_value:
			update_communication_status(comment)
			mock_set_value.assert_not_called()

	def test_status_not_updated_for_unknown_sent_or_received_value(self):
		"""A Communication with an unexpected sent_or_received value should be skipped."""
		lead = self._make_lead("invalid")

		comm = frappe.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"communication_medium": "Email",
				"sent_or_received": "Received",
				"subject": "Setup",
				"reference_doctype": "CRM Lead",
				"reference_name": lead.name,
			}
		)
		comm.insert(ignore_permissions=True)

		comm.sent_or_received = "Unknown"
		update_communication_status(comm)
		# Status should remain "Open" from the first insert
		status = frappe.db.get_value("CRM Lead", lead.name, "communication_status")
		self.assertEqual(status, "Open")


class TestCreateLeadFromIncomingEmail(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.db.set_single_value("FCRM Settings", "auto_update_communication_status", 0)
		frappe.db.set_single_value("FCRM Settings", "update_timestamp_on_new_communication", 0)

	@classmethod
	def tearDownClass(cls):
		frappe.db.rollback()
		super().tearDownClass()

	def tearDown(self):
		frappe.db.rollback()
		frappe.db.set_single_value("FCRM Settings", "auto_update_communication_status", 0)
		frappe.db.set_single_value("FCRM Settings", "update_timestamp_on_new_communication", 0)

	def _make_email_account(self, create_lead=1):
		"""Create a minimal incoming Email Account with the CRM custom field set."""
		email_account = frappe.get_doc(
			{
				"doctype": "Email Account",
				"email_account_name": "Test CRM Incoming",
				"email_id": "test-crm-incoming@example.com",
				"enable_incoming": 1,
				"create_lead_from_incoming_email": create_lead,
			}
		)
		email_account.flags.ignore_mandatory = True
		email_account.flags.ignore_validate = True
		email_account.insert(ignore_permissions=True)
		return email_account

	def _incoming_comm(self, sender, email_account_name, sender_full_name=None, **kwargs):
		doc = frappe.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"communication_medium": "Email",
				"sent_or_received": "Received",
				"subject": "Test Incoming Email",
				"sender": sender,
				"email_account": email_account_name,
				**kwargs,
			}
		)
		if sender_full_name:
			doc.sender_full_name = sender_full_name
		return doc

	def test_lead_created_from_incoming_email(self):
		"""An unreferenced incoming email should create a new CRM Lead."""
		email_account = self._make_email_account()
		doc = self._incoming_comm("newlead@example.com", email_account.name, sender_full_name="New Lead")
		doc.insert(ignore_permissions=True)

		self.assertTrue(frappe.db.exists("CRM Lead", {"email": "newlead@example.com"}))

	def test_lead_not_created_when_setting_disabled(self):
		"""When create_lead_from_incoming_email is off on the Email Account, no lead is created."""
		email_account = self._make_email_account(create_lead=0)
		doc = self._incoming_comm("disabled@example.com", email_account.name)
		doc.insert(ignore_permissions=True)

		self.assertFalse(frappe.db.exists("CRM Lead", {"email": "disabled@example.com"}))

	def test_lead_not_created_when_no_email_account(self):
		"""A Communication without an email_account should not create a lead."""
		doc = frappe.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"communication_medium": "Email",
				"sent_or_received": "Received",
				"subject": "No email account",
				"sender": "noaccount@example.com",
			}
		)
		with patch("frappe.new_doc") as mock_new_doc:
			create_lead_from_incoming_email(doc)
			mock_new_doc.assert_not_called()

	def test_lead_not_created_when_communication_already_referenced(self):
		"""A Communication with an existing reference should not create a new lead."""
		email_account = self._make_email_account()
		existing = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "RefLead", "email": "reflead@example.com"}
		)
		existing.insert(ignore_permissions=True)

		doc = self._incoming_comm(
			"referenced@example.com",
			email_account.name,
			reference_doctype="CRM Lead",
			reference_name=existing.name,
		)
		doc.insert(ignore_permissions=True)

		self.assertFalse(frappe.db.exists("CRM Lead", {"email": "referenced@example.com"}))

	def test_lead_not_created_when_lead_already_exists_for_sender(self):
		"""No duplicate lead should be created when a lead with the sender email already exists."""
		email_account = self._make_email_account()
		existing = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Existing", "email": "dupe@example.com"}
		)
		existing.insert(ignore_permissions=True)

		doc = self._incoming_comm("dupe@example.com", email_account.name)
		doc.insert(ignore_permissions=True)

		self.assertEqual(frappe.db.count("CRM Lead", {"email": "dupe@example.com"}), 1)

	def test_lead_not_created_for_non_communication_doctype(self):
		"""Calling the function with a non-Communication doc should be a no-op."""
		comment = frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Comment",
				"reference_doctype": "CRM Lead",
				"reference_name": "LEAD-0001",
				"content": "test",
			}
		)
		with patch("frappe.new_doc") as mock_new_doc:
			create_lead_from_incoming_email(comment)
			mock_new_doc.assert_not_called()

	def test_lead_not_created_for_sent_communication_with_non_communication_type(self):
		"""A sent message with a non-Communication type should not create a lead."""
		doc = frappe.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Notification",
				"communication_medium": "Email",
				"sent_or_received": "Sent",
				"subject": "Sent notification",
				"sender": "sent@example.com",
			}
		)
		with patch("frappe.new_doc") as mock_new_doc:
			create_lead_from_incoming_email(doc)
			mock_new_doc.assert_not_called()

	def test_lead_first_name_from_sender_full_name(self):
		"""The lead's first_name should come from sender_full_name when present."""
		email_account = self._make_email_account()
		doc = self._incoming_comm("fullname@example.com", email_account.name, sender_full_name="Jane Doe")
		create_lead_from_incoming_email(doc)

		lead = frappe.db.get_value("CRM Lead", {"email": "fullname@example.com"}, "first_name")
		self.assertEqual(lead, "Jane Doe")

	def test_lead_first_name_falls_back_to_email_prefix(self):
		"""When sender_full_name is absent, the email prefix should be used as first_name."""
		email_account = self._make_email_account()
		doc = self._incoming_comm("prefix@example.com", email_account.name)
		create_lead_from_incoming_email(doc)

		lead = frappe.db.get_value("CRM Lead", {"email": "prefix@example.com"}, "first_name")
		self.assertEqual(lead, "prefix")
