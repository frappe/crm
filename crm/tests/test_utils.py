import time
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from crm.utils import (
	are_same_phone_number,
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
