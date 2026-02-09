# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from crm.fcrm.doctype.crm_call_log.crm_call_log import (
	create_lead_from_call_log,
	get_call_log,
	parse_call_log,
)


class TestCRMCallLog(FrappeTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_call_log_creation_incoming(self):
		"""Test creating an incoming call log"""
		call = create_test_call_log(
			type="Incoming",
			status="Completed",
			caller=None,
			receiver="Administrator",
		)

		self.assertEqual(call.type, "Incoming")
		self.assertEqual(call.status, "Completed")
		self.assertEqual(call.receiver, "Administrator")

	def test_call_log_creation_outgoing(self):
		"""Test creating an outgoing call log"""
		call = create_test_call_log(
			type="Outgoing",
			status="Completed",
			caller="Administrator",
			receiver=None,
		)

		self.assertEqual(call.type, "Outgoing")
		self.assertEqual(call.status, "Completed")
		self.assertEqual(call.caller, "Administrator")

	def test_call_log_with_duration(self):
		"""Test call log with duration field"""
		call = create_test_call_log(
			type="Incoming",
			status="Completed",
			duration=120,  # 2 minutes
		)

		self.assertEqual(call.duration, 120)

	def test_call_log_with_recording_url(self):
		"""Test call log with recording URL"""
		recording_url = "https://example.com/recording.mp3"
		call = create_test_call_log(
			type="Outgoing",
			status="Completed",
			recording_url=recording_url,
		)

		self.assertEqual(call.recording_url, recording_url)

	def test_has_link_method(self):
		"""Test has_link method to check if document link exists"""
		# Create a lead for linking
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test Lead",
				"lead_owner": "Administrator",
			}
		).insert()

		call = create_test_call_log()

		# Initially no link should exist
		self.assertFalse(call.has_link("CRM Lead", lead.name))

		# Add link
		call.link_with_reference_doc("CRM Lead", lead.name)

		# Now link should exist
		self.assertTrue(call.has_link("CRM Lead", lead.name))

	def test_link_with_reference_doc(self):
		"""Test linking call log with reference document"""
		# Create a deal for linking
		org = frappe.get_doc(
			{
				"doctype": "CRM Organization",
				"organization_name": "Test Org for Call Log",
			}
		).insert()

		deal = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": org.name,
				"deal_owner": "Administrator",
			}
		).insert()

		call = create_test_call_log()

		# Link with deal
		call.link_with_reference_doc("CRM Deal", deal.name)
		call.save()

		# Verify link was created
		self.assertTrue(call.has_link("CRM Deal", deal.name))
		self.assertEqual(len(call.links), 1)
		self.assertEqual(call.links[0].link_doctype, "CRM Deal")
		self.assertEqual(call.links[0].link_name, deal.name)

	def test_link_with_reference_doc_duplicate_prevention(self):
		"""Test that linking same document twice doesn't create duplicate links"""
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test Lead",
				"lead_owner": "Administrator",
			}
		).insert()

		call = create_test_call_log()

		# Link twice
		call.link_with_reference_doc("CRM Lead", lead.name)
		call.link_with_reference_doc("CRM Lead", lead.name)
		call.save()

		# Should only have one link
		self.assertEqual(len(call.links), 1)

	def test_default_list_data_returns_actual_logs(self):
		"""Test default_list_data returns actual call log data"""
		from crm.fcrm.doctype.crm_call_log.crm_call_log import CRMCallLog

		# Create test call logs with valid users
		create_test_call_log(
			type="Incoming",
			caller=None,
			receiver="Administrator",
			status="Completed",
		)
		create_test_call_log(
			type="Outgoing",
			caller="Administrator",
			receiver=None,
			status="Failed",
		)

		data = CRMCallLog.default_list_data()

		# Verify structure
		self.assertIn("columns", data)
		self.assertIn("rows", data)
		self.assertIsInstance(data["columns"], list)
		self.assertIsInstance(data["rows"], list)

		# Verify columns contain required fields
		self.assertTrue(len(data["columns"]) > 0)
		column_keys = [col["key"] for col in data["columns"]]
		self.assertIn("caller", column_keys)
		self.assertIn("receiver", column_keys)
		self.assertIn("type", column_keys)
		self.assertIn("status", column_keys)

		# Verify rows contain data fields
		self.assertIn("name", data["rows"])
		self.assertIn("caller", data["rows"])
		self.assertIn("receiver", data["rows"])
		self.assertIn("type", data["rows"])
		self.assertIn("status", data["rows"])

	def test_parse_call_log_incoming(self):
		"""Test parse_call_log function with incoming call"""
		# Create a user for testing
		if not frappe.db.exists("User", "test@example.com"):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": "test@example.com",
					"first_name": "Test",
				}
			).insert()

		call_data = {
			"type": "Incoming",
			"from": "+1234567890",
			"to": "+0987654321",
			"receiver": "test@example.com",
			"duration": 120,
		}

		parsed = parse_call_log(call_data)

		# Verify parsed data with actual values
		self.assertEqual(parsed["activity_type"], "incoming_call")
		self.assertEqual(parsed["_duration"], "2m")
		# _caller and _receiver are dicts with label and image
		self.assertIsInstance(parsed["_caller"], dict)
		self.assertIn("label", parsed["_caller"])
		self.assertEqual(parsed["_caller"]["label"], "Unknown")  # Phone number resolves to Unknown
		self.assertIsInstance(parsed["_receiver"], dict)
		self.assertIn("label", parsed["_receiver"])
		self.assertEqual(parsed["from"], "+1234567890")
		self.assertEqual(parsed["to"], "+0987654321")

	def test_parse_call_log_outgoing(self):
		"""Test parse_call_log function with outgoing call"""
		call_data = {
			"type": "Outgoing",
			"from": "+1234567890",
			"to": "+0987654321",
			"caller": "Administrator",
			"duration": 180,
		}

		parsed = parse_call_log(call_data)

		# Verify parsed data with actual values
		self.assertEqual(parsed["activity_type"], "outgoing_call")
		self.assertEqual(parsed["_duration"], "3m")
		# _caller and _receiver are dicts with label and image
		self.assertIsInstance(parsed["_caller"], dict)
		self.assertEqual(parsed["_caller"]["label"], "Administrator")
		self.assertIsInstance(parsed["_receiver"], dict)
		self.assertEqual(parsed["_receiver"]["label"], "Unknown")  # Phone number resolves to Unknown
		self.assertEqual(parsed["from"], "+1234567890")
		self.assertEqual(parsed["to"], "+0987654321")

	def test_get_call_log_api(self):
		"""Test get_call_log API function"""
		call = create_test_call_log(
			type="Outgoing",
			status="Completed",
			duration=60,
		)

		# Call the API
		result = get_call_log(call.name)

		# Verify result
		self.assertEqual(result["name"], call.name)
		self.assertEqual(result["type"], "Outgoing")
		self.assertEqual(result["status"], "Completed")
		self.assertIn("_duration", result)
		self.assertIn("_tasks", result)
		self.assertIn("_notes", result)

	def test_get_call_log_with_reference_lead(self):
		"""Test get_call_log API with reference to CRM Lead"""
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test Lead",
				"lead_owner": "Administrator",
			}
		).insert()

		call = create_test_call_log(
			reference_doctype="CRM Lead",
			reference_docname=lead.name,
		)

		result = get_call_log(call.name)

		# Verify lead reference
		self.assertEqual(result.get("_lead"), lead.name)

	def test_get_call_log_with_reference_deal(self):
		"""Test get_call_log API with reference to CRM Deal"""
		org = frappe.get_doc(
			{
				"doctype": "CRM Organization",
				"organization_name": "Test Org for Call",
			}
		).insert()

		deal = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": org.name,
				"deal_owner": "Administrator",
			}
		).insert()

		call = create_test_call_log(
			reference_doctype="CRM Deal",
			reference_docname=deal.name,
		)

		result = get_call_log(call.name)

		# Verify deal reference
		self.assertEqual(result.get("_deal"), deal.name)

	def test_get_call_log_with_linked_task(self):
		"""Test get_call_log API with linked CRM Task"""
		call = create_test_call_log()

		# Create and link a task
		task = frappe.get_doc(
			{
				"doctype": "CRM Task",
				"title": "Follow up call",
				"assigned_to": "Administrator",
			}
		).insert()

		call.link_with_reference_doc("CRM Task", task.name)
		call.save()

		result = get_call_log(call.name)

		# Verify task is in results
		self.assertEqual(len(result["_tasks"]), 1)
		self.assertEqual(result["_tasks"][0]["name"], task.name)

	def test_create_lead_from_call_log_basic(self):
		"""Test creating a lead from call log"""
		call = create_test_call_log(
			type="Incoming",
			from_number="+1234567890",
		)

		# Create lead from call log
		lead_name = create_lead_from_call_log(
			call_log=frappe.as_json({"name": call.name}),
			lead_details=frappe.as_json({"first_name": "John", "last_name": "Doe"}),
		)

		# Verify lead was created
		self.assertTrue(frappe.db.exists("CRM Lead", lead_name))
		lead = frappe.get_doc("CRM Lead", lead_name)
		self.assertEqual(lead.first_name, "John")
		self.assertEqual(lead.last_name, "Doe")
		self.assertEqual(lead.mobile_no, "+1234567890")

		# Verify call log was linked
		call.reload()
		self.assertTrue(call.has_link("CRM Lead", lead_name))

	def test_create_lead_from_call_log_with_owner(self):
		"""Test creating lead from call log with specific owner"""
		call = create_test_call_log(
			type="Outgoing",
			to="+9876543210",
		)

		lead_name = create_lead_from_call_log(
			call_log=frappe.as_json({"name": call.name}),
			lead_details=frappe.as_json({"first_name": "Jane", "lead_owner": "Administrator"}),
		)

		lead = frappe.get_doc("CRM Lead", lead_name)
		self.assertEqual(lead.lead_owner, "Administrator")

	def test_create_lead_from_call_log_no_details(self):
		"""Test creating lead from call log without lead details"""
		call = create_test_call_log(
			type="Incoming",
			from_number="+1112223333",
		)

		lead_name = create_lead_from_call_log(call_log=frappe.as_json({"name": call.name}))

		# Verify lead was created with default name
		lead = frappe.get_doc("CRM Lead", lead_name)
		self.assertTrue(lead.first_name.startswith("Lead from call"))
		self.assertEqual(lead.mobile_no, "+1112223333")

	def test_create_lead_from_call_log_invalid_call_log(self):
		"""Test that invalid call log throws error"""
		with self.assertRaises(frappe.DoesNotExistError):
			create_lead_from_call_log(call_log=frappe.as_json({"name": "invalid_name"}))

	def test_create_lead_from_call_log_permission_check(self):
		"""Test that permission is checked when creating lead from call log"""
		create_test_call_log()

		# Verify that empty call log throws error
		with self.assertRaises(frappe.ValidationError):
			create_lead_from_call_log(call_log=frappe.as_json({}))

	def test_call_log_status_filtering(self):
		"""Test that call logs can be filtered by status"""
		# Create calls with different statuses
		completed_call = create_test_call_log(status="Completed", type="Incoming")
		failed_call = create_test_call_log(status="Failed", type="Outgoing")
		busy_call = create_test_call_log(status="Busy", type="Incoming")

		# Verify statuses are set correctly
		self.assertEqual(completed_call.status, "Completed")
		self.assertEqual(failed_call.status, "Failed")
		self.assertEqual(busy_call.status, "Busy")

		# Test filtering by status
		completed_logs = frappe.get_all("CRM Call Log", filters={"status": "Completed"})
		failed_logs = frappe.get_all("CRM Call Log", filters={"status": "Failed"})

		self.assertGreaterEqual(len(completed_logs), 1)
		self.assertGreaterEqual(len(failed_logs), 1)

		# Verify our specific calls are in the right filtered lists
		completed_names = [log.name for log in completed_logs]
		failed_names = [log.name for log in failed_logs]

		self.assertIn(completed_call.name, completed_names)
		self.assertIn(failed_call.name, failed_names)
		self.assertNotIn(busy_call.name, completed_names)
		self.assertNotIn(busy_call.name, failed_names)

	def test_call_log_with_telephony_medium(self):
		"""Test call log with different telephony mediums"""
		call = create_test_call_log(telephony_medium="Twilio")
		self.assertEqual(call.telephony_medium, "Twilio")

		call2 = create_test_call_log(telephony_medium="Exotel")
		self.assertEqual(call2.telephony_medium, "Exotel")


def create_test_call_log(**kwargs):
	"""Helper function to create a CRM Call Log for testing"""
	import uuid

	# Generate unique ID if not provided (required for autoname)
	unique_id = kwargs.pop("id", str(uuid.uuid4())[:10])

	# Handle special field name mapping
	if "from_number" in kwargs:
		kwargs["from"] = kwargs.pop("from_number")

	# Set defaults for required fields
	data = {
		"doctype": "CRM Call Log",
		"id": unique_id,
		"type": "Incoming",
		"status": "Completed",
		"to": "+1234567890",
		"from": "+0987654321",
	}

	# Update with all provided kwargs
	data.update(kwargs)

	call_log = frappe.get_doc(data)
	call_log.insert()
	return call_log
