# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from crm.fcrm.doctype.crm_deal.crm_deal import (
	add_contact,
	create_deal,
	remove_contact,
	set_primary_contact,
)


class TestCRMDeal(FrappeTestCase):
	def tearDown(self) -> None:
		frappe.db.rollback()

	def test_deal_creation_with_organization(self):
		"""Test creating a deal with organization"""
		deal = create_test_deal(
			organization="Test Org Inc",
			annual_revenue=1000000,
			status="Qualification",
		)

		self.assertTrue(deal.name)
		self.assertTrue(deal.organization)
		self.assertEqual(deal.annual_revenue, 1000000)

	def test_set_primary_contact(self):
		"""Test setting primary contact from contacts table"""
		# Create contacts
		contact1 = create_test_contact(first_name="John", last_name="Doe", email="john@example.com")
		contact2 = create_test_contact(
			first_name="Jane", last_name="Smith", email="jane@example.com", mobile_no="+1234567890"
		)

		# Create deal with two contacts
		deal = create_test_deal(organization="Contact Test Org")
		deal.append("contacts", {"contact": contact1.name})
		deal.append("contacts", {"contact": contact2.name, "is_primary": 1})
		deal.save()

		# Verify primary contact is set
		deal.reload()
		primary_contacts = [c for c in deal.contacts if c.is_primary == 1]
		self.assertEqual(len(primary_contacts), 1)
		self.assertEqual(primary_contacts[0].contact, contact2.name)

	def test_set_primary_email_mobile_no(self):
		"""Test that email and mobile are set from primary contact"""
		# Create contact
		contact = create_test_contact(
			first_name="Test",
			last_name="User",
			email="testuser@example.com",
			mobile_no="+9876543210",
			phone="+1111111111",
		)

		# Create deal with contact
		deal = create_test_deal(organization="Email Test Org")
		deal.append("contacts", {"contact": contact.name, "is_primary": 1})
		deal.save()

		# Verify email and mobile are set from contact
		deal.reload()
		self.assertEqual(deal.email, "testuser@example.com")
		self.assertEqual(deal.mobile_no, "+9876543210")
		self.assertEqual(deal.phone, "+1111111111")

	def test_multiple_primary_contacts_error(self):
		"""Test that having multiple primary contacts throws error"""
		contact1 = create_test_contact(first_name="Primary1", email="p1@example.com")
		contact2 = create_test_contact(first_name="Primary2", email="p2@example.com")

		deal = create_test_deal(organization="Multiple Primary Test")
		deal.append("contacts", {"contact": contact1.name, "is_primary": 1})
		deal.append("contacts", {"contact": contact2.name, "is_primary": 1})

		with self.assertRaises(frappe.exceptions.ValidationError) as context:
			deal.save()
		self.assertIn("Only one", str(context.exception))

	def test_no_primary_contact_clears_email(self):
		"""Test that email/mobile on deal (not child table) are cleared when no primary contact"""
		contact1 = create_test_contact(
			first_name="Primary", email="primary@example.com", mobile_no="+1111111111"
		)
		contact2 = create_test_contact(first_name="NonPrimary", email="nonprimary@example.com")

		# Create deal with primary contact - email should be set
		deal = create_test_deal(
			organization="No Primary Org",
			expected_deal_value=1000,
			expected_closure_date="2026-12-31",
		)
		deal.append("contacts", {"contact": contact1.name, "is_primary": 1})
		deal.save()
		deal.reload()

		self.assertEqual(deal.email, "primary@example.com")
		self.assertEqual(deal.mobile_no, "+1111111111")

		# Change to non-primary contact - deal email should be cleared
		for c in deal.contacts:
			c.is_primary = 0
		deal.append("contacts", {"contact": contact2.name, "is_primary": 0})
		deal.save()
		deal.reload()

		# Deal-level fields should be cleared since no primary contact
		self.assertEqual(deal.email, "")
		self.assertEqual(deal.mobile_no, "")
		self.assertEqual(deal.phone, "")

	def test_deal_owner_assignment(self):
		"""Test that deal owner is assigned on creation"""
		deal = create_test_deal(organization="Owner Test Org", deal_owner="Administrator")

		# Verify deal owner is assigned
		assignees = deal.get_assigned_users()
		self.assertIn("Administrator", assignees)

	def test_update_deal_owner(self):
		"""Test updating deal owner assigns and shares with new owner"""
		# Create deal without owner
		deal = create_test_deal(organization="Update Owner Org")
		self.assertFalse(deal.deal_owner)

		# Update deal owner
		deal.deal_owner = "Administrator"
		deal.save()

		# Verify assignment and share
		deal.reload()
		self.assertEqual(deal.deal_owner, "Administrator")
		assignees = deal.get_assigned_users()
		self.assertIn("Administrator", assignees)

		docshare = frappe.db.exists(
			"DocShare",
			{"user": "Administrator", "share_name": deal.name, "share_doctype": "CRM Deal"},
		)
		self.assertTrue(docshare)

		# Try to assign same agent again - should not duplicate
		initial_count = len(assignees)
		deal.assign_agent("Administrator")
		assignees_after = deal.get_assigned_users()
		self.assertEqual(len(assignees_after), initial_count)

	def test_add_contact_api(self):
		"""Test add_contact API function"""
		deal = create_test_deal(organization="Add Contact Org")
		contact = create_test_contact(first_name="API", last_name="User", email="api@example.com")

		# Add contact using API
		result = add_contact(deal.name, contact.name)
		self.assertTrue(result)

		# Verify contact was added
		deal.reload()
		contact_names = [c.contact for c in deal.contacts]
		self.assertIn(contact.name, contact_names)

	def test_remove_contact_api(self):
		"""Test remove_contact API function"""
		contact = create_test_contact(first_name="Remove", email="remove@example.com")
		deal = create_test_deal(organization="Remove Contact Org")
		deal.append("contacts", {"contact": contact.name})
		deal.save()

		# Verify contact exists
		deal.reload()
		self.assertEqual(len(deal.contacts), 1)

		# Remove contact using API
		result = remove_contact(deal.name, contact.name)
		self.assertTrue(result)

		# Verify contact was removed
		deal.reload()
		self.assertEqual(len(deal.contacts), 0)

	def test_set_primary_contact_api(self):
		"""Test set_primary_contact API function"""
		contact1 = create_test_contact(first_name="First", email="first@example.com")
		contact2 = create_test_contact(first_name="Second", email="second@example.com")

		deal = create_test_deal(organization="Primary API Org")
		deal.append("contacts", {"contact": contact1.name, "is_primary": 1})
		deal.append("contacts", {"contact": contact2.name})
		deal.save()

		# Change primary contact using API
		result = set_primary_contact(deal.name, contact2.name)
		self.assertTrue(result)

		# Verify primary contact was changed
		deal.reload()
		for c in deal.contacts:
			if c.contact == contact2.name:
				self.assertEqual(c.is_primary, 1)
			else:
				self.assertEqual(c.is_primary, 0)

	def test_create_deal_api(self):
		"""Test create_deal API function"""
		deal_name = create_deal(
			{
				"organization_name": "API Deal Org",
				"annual_revenue": 500000,
				"first_name": "Deal",
				"last_name": "Creator",
				"email": "dealcreator@example.com",
				"mobile_no": "+5555555555",
			}
		)

		self.assertTrue(deal_name)

		# Verify deal was created
		deal = frappe.get_doc("CRM Deal", deal_name)
		self.assertEqual(deal.annual_revenue, 500000)
		self.assertTrue(deal.organization)
		self.assertTrue(len(deal.contacts) > 0)

		# Verify organization was created
		org = frappe.get_doc("CRM Organization", deal.organization)
		self.assertEqual(org.organization_name, "API Deal Org")

		# Verify contact was created
		contact = frappe.get_doc("Contact", deal.contacts[0].contact)
		self.assertEqual(contact.first_name, "Deal")
		self.assertEqual(contact.email_id, "dealcreator@example.com")

	def test_create_deal_with_existing_organization(self):
		"""Test create_deal with existing organization"""
		# Create organization first
		org = frappe.get_doc(
			{
				"doctype": "CRM Organization",
				"organization_name": "Existing Org",
				"annual_revenue": 2000000,
			}
		).insert()

		# Create deal with same organization name
		deal_name = create_deal(
			{
				"organization_name": "Existing Org",
				"first_name": "Existing",
				"email": "existing@example.com",
			}
		)

		deal = frappe.get_doc("CRM Deal", deal_name)
		self.assertEqual(deal.organization, org.name)

	def test_create_deal_with_existing_contact(self):
		"""Test create_deal with existing contact"""
		# Create contact first
		contact = create_test_contact(
			first_name="Existing", last_name="Contact", email="existingc@example.com"
		)

		# Create deal with same email
		deal_name = create_deal(
			{
				"organization_name": "Contact Existing Org",
				"first_name": "Existing",
				"email": "existingc@example.com",
			}
		)

		deal = frappe.get_doc("CRM Deal", deal_name)
		self.assertEqual(deal.contacts[0].contact, contact.name)

	def test_validate_lost_reason_required(self):
		"""Test that lost reason is required when status is Lost"""
		# Create Lost status if not exists
		if not frappe.db.exists("CRM Deal Status", "Lost"):
			frappe.get_doc({"doctype": "CRM Deal Status", "name": "Lost", "type": "Lost"}).insert()

		deal = create_test_deal(organization="Lost Deal Org")

		# Try to set status to Lost without lost_reason
		deal.status = "Lost"
		with self.assertRaises(frappe.exceptions.ValidationError) as context:
			deal.save()
		self.assertIn("reason for losing", str(context.exception))

	def test_validate_lost_reason_other(self):
		"""Test that lost_notes is required when lost_reason is Other"""
		if not frappe.db.exists("CRM Deal Status", "Lost"):
			frappe.get_doc({"doctype": "CRM Deal Status", "name": "Lost", "type": "Lost"}).insert()

		if not frappe.db.exists("CRM Lost Reason", "Other"):
			frappe.get_doc({"doctype": "CRM Lost Reason", "reason": "Other"}).insert()

		deal = create_test_deal(organization="Lost Notes Org")
		deal.status = "Lost"
		deal.lost_reason = "Other"

		with self.assertRaises(frappe.exceptions.ValidationError) as context:
			deal.save()
		self.assertIn("specify the reason", str(context.exception))

	def test_closed_date_set_on_won(self):
		"""Test that closed_date is set when status is Won"""
		if not frappe.db.exists("CRM Deal Status", "Won"):
			frappe.get_doc({"doctype": "CRM Deal Status", "name": "Won", "type": "Won"}).insert()

		deal = create_test_deal(
			organization="Won Deal Org", expected_deal_value=10000, expected_closure_date="2026-12-31"
		)
		self.assertFalse(deal.closed_date)

		deal.status = "Won"
		deal.save()

		deal.reload()
		self.assertTrue(deal.closed_date)

	def test_forecasting_fields_validation(self):
		"""Test forecasting fields validation when enabled"""
		# Enable forecasting
		settings = frappe.get_single("FCRM Settings")
		original_value = settings.enable_forecasting
		settings.enable_forecasting = 1
		settings.save()

		try:
			# Should fail without expected_deal_value
			with self.assertRaises(frappe.exceptions.MandatoryError):
				create_test_deal(organization="Forecast Org")

			# Should fail without expected_closure_date
			with self.assertRaises(frappe.exceptions.MandatoryError):
				create_test_deal(organization="Forecast Org 2", expected_deal_value=5000)

			# Should succeed with both fields
			deal = create_test_deal(
				organization="Forecast Org 3",
				expected_deal_value=5000,
				expected_closure_date="2026-12-31",
			)
			self.assertTrue(deal.name)

		finally:
			# Restore original setting
			settings.enable_forecasting = original_value
			settings.save()

	def test_single_contact_auto_primary(self):
		"""Test that single contact is automatically set as primary"""
		contact = create_test_contact(first_name="Auto", email="auto@example.com")
		deal = create_test_deal(organization="Auto Primary Org")
		deal.append("contacts", {"contact": contact.name})
		deal.save()

		deal.reload()
		self.assertEqual(deal.contacts[0].is_primary, 1)


def create_test_deal(**kwargs):
	"""Helper function to create a CRM Deal for testing"""
	# Create organization if provided as string
	if "organization" in kwargs and isinstance(kwargs["organization"], str):
		org_name = kwargs["organization"]
		if not frappe.db.exists("CRM Organization", {"organization_name": org_name}):
			org = frappe.get_doc({"doctype": "CRM Organization", "organization_name": org_name}).insert()
			kwargs["organization"] = org.name
		else:
			kwargs["organization"] = frappe.db.get_value(
				"CRM Organization", {"organization_name": org_name}, "name"
			)

	data = {"doctype": "CRM Deal"}
	data.update(kwargs)
	return frappe.get_doc(data).insert()


def create_test_contact(**kwargs):
	"""Helper function to create a Contact for testing"""
	contact = frappe.get_doc({"doctype": "Contact"})
	contact.update(kwargs)

	if kwargs.get("email"):
		contact.append("email_ids", {"email_id": kwargs["email"], "is_primary": 1})

	if kwargs.get("mobile_no"):
		contact.append("phone_nos", {"phone": kwargs["mobile_no"], "is_primary_mobile_no": 1})

	if kwargs.get("phone"):
		contact.append("phone_nos", {"phone": kwargs["phone"], "is_primary_phone": 1})

	contact.insert(ignore_permissions=True)
	return contact
