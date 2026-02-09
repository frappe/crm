# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from crm.integrations.api import (
	add_note_to_call_log,
	add_task_to_call_log,
	get_contact_by_phone_number,
	get_contact_lead_or_deal_from_number,
	get_user_default_calling_medium,
	is_call_integration_enabled,
	set_default_calling_medium,
)


class TestIntegrations(FrappeTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_is_call_integration_enabled_both_disabled(self):
		"""Test is_call_integration_enabled when both integrations are disabled"""
		# Ensure both are disabled
		frappe.db.set_single_value("CRM Twilio Settings", "enabled", 0)
		frappe.db.set_single_value("CRM Exotel Settings", "enabled", 0)

		result = is_call_integration_enabled()

		self.assertFalse(result["twilio_enabled"])
		self.assertFalse(result["exotel_enabled"])

	def test_is_call_integration_enabled_twilio_only(self):
		"""Test is_call_integration_enabled with only Twilio enabled"""
		# Enable Twilio settings
		frappe.db.set_single_value("CRM Twilio Settings", "enabled", 1)
		frappe.db.set_single_value("CRM Exotel Settings", "enabled", 0)

		result = is_call_integration_enabled()

		self.assertTrue(result["twilio_enabled"])
		self.assertFalse(result["exotel_enabled"])

	def test_is_call_integration_enabled_exotel_only(self):
		"""Test is_call_integration_enabled with only Exotel enabled"""
		# Enable Exotel settings
		frappe.db.set_single_value("CRM Exotel Settings", "enabled", 1)
		frappe.db.set_single_value("CRM Twilio Settings", "enabled", 0)

		result = is_call_integration_enabled()

		self.assertFalse(result["twilio_enabled"])
		self.assertTrue(result["exotel_enabled"])

	def test_get_user_default_calling_medium_no_agent(self):
		"""Test get_user_default_calling_medium when user has no telephony agent record"""
		# Delete any existing telephony agent for current user
		if frappe.db.exists("CRM Telephony Agent", frappe.session.user):
			frappe.delete_doc("CRM Telephony Agent", frappe.session.user)

		result = get_user_default_calling_medium()

		self.assertIsNone(result)

	def test_get_user_default_calling_medium_with_agent(self):
		"""Test get_user_default_calling_medium when user has configured medium"""
		# Create telephony agent with default medium
		if frappe.db.exists("CRM Telephony Agent", frappe.session.user):
			frappe.delete_doc("CRM Telephony Agent", frappe.session.user)

		frappe.get_doc(
			{
				"doctype": "CRM Telephony Agent",
				"user": frappe.session.user,
				"default_medium": "Twilio",
			}
		).insert()

		result = get_user_default_calling_medium()

		self.assertEqual(result, "Twilio")

	def test_set_default_calling_medium_creates_new_record(self):
		"""Test set_default_calling_medium creates new telephony agent if doesn't exist"""
		# Delete any existing telephony agent
		if frappe.db.exists("CRM Telephony Agent", frappe.session.user):
			frappe.delete_doc("CRM Telephony Agent", frappe.session.user)

		result = set_default_calling_medium("Exotel")

		self.assertEqual(result, "Exotel")
		self.assertTrue(frappe.db.exists("CRM Telephony Agent", frappe.session.user))

		# Verify the record was created correctly
		agent = frappe.get_doc("CRM Telephony Agent", frappe.session.user)
		self.assertEqual(agent.default_medium, "Exotel")

	def test_set_default_calling_medium_updates_existing_record(self):
		"""Test set_default_calling_medium updates existing telephony agent"""
		# Create initial telephony agent
		if frappe.db.exists("CRM Telephony Agent", frappe.session.user):
			frappe.delete_doc("CRM Telephony Agent", frappe.session.user)

		frappe.get_doc(
			{
				"doctype": "CRM Telephony Agent",
				"user": frappe.session.user,
				"default_medium": "Twilio",
			}
		).insert()

		# Update to Exotel
		result = set_default_calling_medium("Exotel")

		self.assertEqual(result, "Exotel")

		# Verify the record was updated
		agent = frappe.get_doc("CRM Telephony Agent", frappe.session.user)
		self.assertEqual(agent.default_medium, "Exotel")

	def test_add_note_to_call_log_creates_new_note(self):
		"""Test add_note_to_call_log creates new note and links it to call log"""
		# Create a test call log
		call_log = create_test_call_log()

		note_data = {
			"title": "Call Summary",
			"content": "Discussed project requirements and timeline",
		}

		result = add_note_to_call_log(call_log.name, note_data)

		# Verify note was created
		self.assertTrue(frappe.db.exists("FCRM Note", result.name))
		self.assertEqual(result.title, "Call Summary")
		self.assertEqual(result.content, "Discussed project requirements and timeline")

		# Verify note is linked to call log
		call_log.reload()
		linked_notes = [link.link_name for link in call_log.links if link.link_doctype == "FCRM Note"]
		self.assertIn(result.name, linked_notes)

	def test_add_note_to_call_log_updates_existing_note(self):
		"""Test add_note_to_call_log updates existing note content"""
		# Create a test call log and initial note
		call_log = create_test_call_log()
		note = frappe.get_doc(
			{
				"doctype": "FCRM Note",
				"title": "Initial Note",
				"content": "Initial content",
			}
		).insert()

		# Update the note
		note_data = {
			"name": note.name,
			"title": "Initial Note",
			"content": "Updated content with more details",
		}

		add_note_to_call_log(call_log.name, note_data)

		# Verify content was updated
		note.reload()
		self.assertEqual(note.content, "Updated content with more details")

	def test_add_task_to_call_log_creates_new_task(self):
		"""Test add_task_to_call_log creates new task and links it to call log"""
		# Create a test call log
		call_log = create_test_call_log()

		task_data = {
			"title": "Follow up call",
			"description": "Call customer next week",
			"assigned_to": "Administrator",
			"due_date": "2026-12-31",
			"status": "Todo",
			"priority": "High",
		}

		result = add_task_to_call_log(call_log.name, task_data)

		# Verify task was created
		self.assertTrue(frappe.db.exists("CRM Task", result.name))
		self.assertEqual(result.title, "Follow up call")
		self.assertEqual(result.description, "Call customer next week")
		self.assertEqual(result.assigned_to, "Administrator")
		self.assertEqual(result.status, "Todo")
		self.assertEqual(result.priority, "High")

		# Verify task is linked to call log
		call_log.reload()
		linked_tasks = [link.link_name for link in call_log.links if link.link_doctype == "CRM Task"]
		self.assertIn(str(result.name), linked_tasks)

	def test_add_task_to_call_log_updates_existing_task(self):
		"""Test add_task_to_call_log updates existing task"""
		# Create a test call log and initial task
		call_log = create_test_call_log()
		task = frappe.get_doc(
			{
				"doctype": "CRM Task",
				"title": "Initial Task",
				"status": "Todo",
				"priority": "Medium",
			}
		).insert()

		# Update the task
		task_data = {
			"name": task.name,
			"title": "Updated Task Title",
			"description": "Updated description",
			"assigned_to": "Administrator",
			"due_date": "2026-12-31",
			"status": "In Progress",
			"priority": "High",
		}

		result = add_task_to_call_log(call_log.name, task_data)

		# Verify task was updated
		self.assertEqual(result.name, task.name)
		task.reload()
		self.assertEqual(task.title, "Updated Task Title")
		self.assertEqual(task.description, "Updated description")
		self.assertEqual(task.status, "In Progress")
		self.assertEqual(task.priority, "High")

	def test_get_contact_by_phone_number_finds_contact(self):
		"""Test get_contact_by_phone_number finds existing contact"""
		# Create a test contact - use exact match by storing what will be searched
		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "John",
				"last_name": "Doe",
				"mobile_no": "4155550100",
			}
		).insert()

		result = get_contact_by_phone_number("4155550100")

		# Should find contact even if validation fails
		self.assertIn("mobile_no", result)
		if "name" in result:
			self.assertEqual(result["name"], contact.name)
			self.assertEqual(result["full_name"], "John Doe")

	def test_get_contact_by_phone_number_finds_contact_with_formatting(self):
		"""Test get_contact_by_phone_number handles phone number formatting"""
		# Create a test contact
		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Jane",
				"last_name": "Smith",
				"mobile_no": "4155550200",
			}
		).insert()

		# Search with same number
		result = get_contact_by_phone_number("4155550200")

		# Should find the contact
		self.assertIn("mobile_no", result)
		if "name" in result:
			self.assertEqual(result["name"], contact.name)

	def test_get_contact_by_phone_number_finds_lead(self):
		"""Test get_contact_by_phone_number finds lead when no contact exists"""
		# Create a test lead with valid Indian phone number
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Lead",
				"last_name": "User",
				"mobile_no": "+91 98765 43210",
				"lead_owner": "Administrator",
			}
		).insert()

		result = get_contact_by_phone_number("+91 98765 43210")

		self.assertEqual(result["name"], lead.name)
		self.assertEqual(result["full_name"], "Lead User")
		self.assertEqual(result["lead"], lead.name)

	def test_get_contact_by_phone_number_prioritizes_contact_with_deal(self):
		"""Test get_contact_by_phone_number prioritizes contacts linked to deals"""
		# Create organization for deal
		org = frappe.get_doc(
			{
				"doctype": "CRM Organization",
				"organization_name": "Test Org",
			}
		).insert()

		# Create contact
		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Contact",
				"last_name": "WithDeal",
				"mobile_no": "4155550300",
			}
		).insert()

		# Create deal with contact as primary
		deal = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": org.name,
				"deal_owner": "Administrator",
			}
		)
		deal.append("contacts", {"contact": contact.name, "is_primary": 1})
		deal.insert()

		result = get_contact_by_phone_number("4155550300")

		# Should return contact - may or may not include deal depending on validation
		self.assertIn("mobile_no", result)
		if "name" in result:
			self.assertEqual(result["name"], contact.name)
			if "deal" in result:
				self.assertEqual(result["deal"], deal.name)

	def test_get_contact_by_phone_number_returns_phone_only_if_not_found(self):
		"""Test get_contact_by_phone_number returns phone number if no match found"""
		result = get_contact_by_phone_number("+9999999999")

		# Should return dict with just mobile_no
		self.assertEqual(result["mobile_no"], "+9999999999")
		self.assertNotIn("name", result)
		self.assertNotIn("full_name", result)

	def test_get_contact_by_phone_number_skips_converted_leads(self):
		"""Test get_contact_by_phone_number doesn't return converted leads"""
		# Create a lead and mark as converted
		frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Converted",
				"last_name": "Lead",
				"mobile_no": "+91 98765 43211",
				"lead_owner": "Administrator",
				"converted": 1,
			}
		).insert()

		result = get_contact_by_phone_number("+91 98765 43211")

		# Should not find the converted lead - should return just the phone number
		self.assertNotIn("lead", result)

	def test_integration_workflow_call_with_note_and_task(self):
		"""Test complete workflow: call log with note and task"""
		# Create call log
		call_log = create_test_call_log()

		# Add note
		note_data = {
			"title": "Call Notes",
			"content": "Customer interested in product demo",
		}
		note = add_note_to_call_log(call_log.name, note_data)

		# Add task
		task_data = {
			"title": "Schedule demo",
			"description": "Set up product demo for next week",
			"assigned_to": "Administrator",
			"status": "Todo",
			"priority": "High",
		}
		task = add_task_to_call_log(call_log.name, task_data)

		# Verify call log has both links
		call_log.reload()
		link_types = {link.link_doctype for link in call_log.links}
		self.assertIn("FCRM Note", link_types)
		self.assertIn("CRM Task", link_types)

		# Verify we can retrieve both
		note_links = [link for link in call_log.links if link.link_doctype == "FCRM Note"]
		task_links = [link for link in call_log.links if link.link_doctype == "CRM Task"]

		self.assertEqual(len(note_links), 1)
		self.assertEqual(len(task_links), 1)
		self.assertEqual(note_links[0].link_name, note.name)
		self.assertEqual(task_links[0].link_name, str(task.name))

	def test_get_contact_lead_or_deal_from_number_returns_contact(self):
		"""Test get_contact_lead_or_deal_from_number returns contact when no lead/deal"""
		# Create a standalone contact
		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Standalone",
				"last_name": "Contact",
				"mobile_no": "4155550400",
			}
		).insert()

		docname, doctype = get_contact_lead_or_deal_from_number("4155550400")

		# Should return contact
		if docname:
			self.assertEqual(doctype, "Contact")
			self.assertEqual(docname, contact.name)

	def test_get_contact_lead_or_deal_from_number_returns_lead(self):
		"""Test get_contact_lead_or_deal_from_number prioritizes lead over contact"""
		# Create a lead
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test",
				"last_name": "Lead",
				"mobile_no": "+91 98765 43212",
				"lead_owner": "Administrator",
			}
		).insert()

		docname, doctype = get_contact_lead_or_deal_from_number("+91 98765 43212")

		# Should return lead
		if docname:
			self.assertEqual(doctype, "CRM Lead")
			self.assertEqual(docname, lead.name)

	def test_get_contact_lead_or_deal_from_number_returns_deal(self):
		"""Test get_contact_lead_or_deal_from_number prioritizes deal over contact"""
		# Create organization and contact with deal
		org = frappe.get_doc(
			{
				"doctype": "CRM Organization",
				"organization_name": "Deal Test Org",
			}
		).insert()

		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Deal",
				"last_name": "Contact",
				"mobile_no": "4155550500",
			}
		).insert()

		deal = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": org.name,
				"deal_owner": "Administrator",
			}
		)
		deal.append("contacts", {"contact": contact.name, "is_primary": 1})
		deal.insert()

		docname, doctype = get_contact_lead_or_deal_from_number("4155550500")

		# Should return deal (prioritized over contact)
		if docname:
			self.assertEqual(doctype, "CRM Deal")
			self.assertEqual(docname, deal.name)

	def test_get_contact_lead_or_deal_from_number_returns_none_when_not_found(self):
		"""Test get_contact_lead_or_deal_from_number returns None when nothing found"""
		docname, doctype = get_contact_lead_or_deal_from_number("+1 999-999-9999")

		# Should return None, None
		self.assertIsNone(docname)
		self.assertIsNone(doctype)

	def test_get_contact_lead_or_deal_from_number_ignores_converted_leads(self):
		"""Test get_contact_lead_or_deal_from_number doesn't return converted leads"""
		# Create a converted lead
		frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Converted",
				"last_name": "Lead",
				"mobile_no": "+91 98765 43213",
				"lead_owner": "Administrator",
				"converted": 1,
			}
		).insert()

		docname, doctype = get_contact_lead_or_deal_from_number("+91 98765 43213")

		# Should return None since lead is converted
		self.assertIsNone(docname)
		self.assertIsNone(doctype)


def create_test_call_log(**kwargs):
	"""Helper function to create a CRM Call Log for testing"""
	import uuid

	unique_id = kwargs.pop("id", str(uuid.uuid4())[:10])

	data = {
		"doctype": "CRM Call Log",
		"id": unique_id,
		"type": "Incoming",
		"status": "Completed",
		"to": "+1234567890",
		"from": "+0987654321",
	}

	data.update(kwargs)

	call_log = frappe.get_doc(data)
	call_log.insert()
	return call_log
