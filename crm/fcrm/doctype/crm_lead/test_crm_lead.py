# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from crm.fcrm.doctype.crm_lead.crm_lead import convert_to_deal


class TestCRMLead(IntegrationTestCase):
	def tearDown(self) -> None:
		frappe.db.rollback()

	def test_lead_creation_with_first_name(self):
		"""Test creating a lead with first name"""
		lead = create_lead(
			first_name="John",
			last_name="Doe",
			email="john.doe@example.com",
			mobile_no="+1234567890",
		)

		self.assertTrue(lead.name)
		self.assertEqual(lead.first_name, "John")
		self.assertEqual(lead.last_name, "Doe")
		self.assertEqual(lead.email, "john.doe@example.com")
		self.assertEqual(lead.lead_name, "John Doe")

	def test_lead_name_with_salutation(self):
		"""Test lead name generation with salutation"""
		lead = create_lead(
			salutation="Mr",
			first_name="James",
			middle_name="Robert",
			last_name="Smith",
			email="james.smith@example.com",
		)

		self.assertEqual(lead.lead_name, "Mr James Robert Smith")
		self.assertEqual(lead.first_name, "James")
		self.assertEqual(lead.middle_name, "Robert")
		self.assertEqual(lead.last_name, "Smith")

	def test_invalid_email_validation(self):
		"""Test that invalid email raises validation error"""
		with self.assertRaises(frappe.exceptions.ValidationError):
			create_lead(
				first_name="Invalid",
				email="not-an-email",
			)

	def test_lead_title_generation(self):
		"""Test that title is set correctly"""
		lead = create_lead(
			first_name="Alice",
			organization="Acme Corp",
			email="alice@acme.com",
		)

		# Title should be organization if provided, otherwise lead_name
		self.assertEqual(lead.title, "Acme Corp")

		lead2 = create_lead(
			first_name="Bob",
			email="bob@example.com",
		)

		self.assertEqual(lead2.title, "Bob")

	def test_lead_owner_cannot_be_same_as_email(self):
		"""Test that lead owner cannot be same as lead email address"""
		with self.assertRaises(frappe.exceptions.ValidationError) as context:
			create_lead(
				first_name="Test",
				email="test@example.com",
				lead_owner="test@example.com",
			)
		self.assertIn("Lead Owner cannot be same as the Lead Email Address", str(context.exception))

	def test_create_contact_from_lead(self):
		"""Test creating a contact from lead data"""
		lead = create_lead(
			first_name="Michael",
			last_name="Jordan",
			email="mj@bulls.com",
			mobile_no="+1234567890",
			phone="+0987654321",
			organization="Chicago Bulls",
			job_title="Player",
			salutation="Mr",
		)

		contact_name = lead.create_contact()
		self.assertTrue(contact_name)

		contact = frappe.get_doc("Contact", contact_name)
		self.assertEqual(contact.first_name, "Michael")
		self.assertEqual(contact.last_name, "Jordan")
		self.assertEqual(contact.email_id, "mj@bulls.com")
		self.assertEqual(contact.mobile_no, "+1234567890")
		self.assertEqual(contact.company_name, "Chicago Bulls")
		self.assertEqual(contact.designation, "Player")

	def test_create_organization_from_lead(self):
		"""Test creating an organization from lead data"""
		lead = create_lead(
			first_name="Steve",
			last_name="Jobs",
			email="steve@apple.com",
			organization="Apple Inc",
			website="https://apple.com",
			annual_revenue=1000000,
		)

		org_name = lead.create_organization()
		self.assertTrue(org_name)

		org = frappe.get_doc("CRM Organization", org_name)
		self.assertEqual(org.organization_name, "Apple Inc")
		self.assertEqual(org.website, "https://apple.com")
		self.assertEqual(org.annual_revenue, 1000000)

	def test_create_organization_with_existing_org(self):
		"""Test that existing organization is reused instead of creating duplicate"""
		# Create first lead with organization
		lead1 = create_lead(
			first_name="Person",
			last_name="One",
			email="person1@example.com",
			organization="Existing Corp",
		)
		org_name1 = lead1.create_organization()

		# Create second lead with same organization
		lead2 = create_lead(
			first_name="Person",
			last_name="Two",
			email="person2@example.com",
			organization="Existing Corp",
		)
		org_name2 = lead2.create_organization()

		# Should return the same organization
		self.assertEqual(org_name1, org_name2)

	def test_contact_exists_with_email(self):
		"""Test checking if contact already exists with same email"""
		lead1 = create_lead(
			first_name="John",
			last_name="Existing",
			email="existing@example.com",
			mobile_no="+1111111111",
		)
		lead1.create_contact()

		lead2 = create_lead(
			first_name="Jane",
			last_name="Duplicate",
			email="existing@example.com",
			mobile_no="+2222222222",
		)

		# Should throw error as contact with same email exists
		with self.assertRaises(frappe.exceptions.ValidationError) as context:
			lead2.create_contact()
		self.assertIn("Contact already exists", str(context.exception))

	def test_convert_lead_to_deal(self):
		"""Test converting a lead to a deal with new contact and organization"""
		lead = create_lead(
			first_name="Deal",
			last_name="Maker",
			email="dealmaker@example.com",
			mobile_no="+1234567890",
			organization="Deal Corp",
			annual_revenue=500000,
		)

		# Convert lead to deal
		deal_name = lead.convert_to_deal()
		self.assertTrue(deal_name)

		# Verify lead is marked as converted
		lead.reload()
		self.assertEqual(lead.converted, 1)

		# Verify deal was created
		deal = frappe.get_doc("CRM Deal", deal_name)
		self.assertEqual(deal.first_name, "Deal")
		self.assertEqual(deal.last_name, "Maker")
		self.assertEqual(deal.lead, lead.name)
		self.assertTrue(deal.organization)

		# Verify contact was created
		self.assertTrue(len(deal.contacts) > 0)
		contact_name = deal.contacts[0].contact
		contact = frappe.get_doc("Contact", contact_name)
		self.assertEqual(contact.first_name, "Deal")
		self.assertEqual(contact.last_name, "Maker")
		self.assertEqual(contact.email_id, "dealmaker@example.com")

		# Verify organization was created
		org = frappe.get_doc("CRM Organization", deal.organization)
		self.assertEqual(org.organization_name, "Deal Corp")
		self.assertEqual(org.annual_revenue, 500000)

	def test_convert_lead_with_existing_contact_and_org(self):
		"""Test converting lead with existing contact and organization"""
		# Create existing contact
		existing_contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Existing",
				"last_name": "Contact",
				"email_ids": [{"email_id": "existing@contact.com", "is_primary": 1}],
			}
		).insert()

		# Create existing organization
		existing_org = frappe.get_doc(
			{
				"doctype": "CRM Organization",
				"organization_name": "Existing Org Inc",
				"annual_revenue": 2000000,
			}
		).insert()

		# Create lead
		lead = create_lead(
			first_name="Existing",
			last_name="Contact",
			email="existing@contact.com",
			organization="Existing Org Inc",
		)

		# Convert lead using existing contact and org
		deal_name = lead.convert_to_deal()

		# Verify deal was created with existing records
		deal = frappe.get_doc("CRM Deal", deal_name)
		self.assertTrue(deal.name)

		# Verify existing contact is linked
		self.assertTrue(len(deal.contacts) > 0)
		self.assertEqual(deal.contacts[0].contact, existing_contact.name)

		# Verify existing organization is linked
		self.assertEqual(deal.organization, existing_org.name)

	def test_convert_to_deal_api(self):
		"""Test convert_to_deal API function"""
		lead = create_lead(
			first_name="API",
			last_name="Test",
			email="apitest@example.com",
			mobile_no="+5555555555",
			organization="API Test Corp",
			annual_revenue=300000,
		)

		# Convert lead to deal using API
		deal_name = convert_to_deal(lead=lead.name)
		self.assertTrue(deal_name)

		# Verify lead is marked as converted
		lead.reload()
		self.assertEqual(lead.converted, 1)

		# Verify deal was created
		deal = frappe.get_doc("CRM Deal", deal_name)
		self.assertEqual(deal.first_name, "API")
		self.assertEqual(deal.last_name, "Test")
		self.assertEqual(deal.lead, lead.name)
		self.assertTrue(deal.organization)

		# Verify contact was created
		self.assertTrue(len(deal.contacts) > 0)
		contact_name = deal.contacts[0].contact
		contact = frappe.get_doc("Contact", contact_name)
		self.assertEqual(contact.first_name, "API")
		self.assertEqual(contact.email_id, "apitest@example.com")

		# Verify organization was created
		org = frappe.get_doc("CRM Organization", deal.organization)
		self.assertEqual(org.organization_name, "API Test Corp")
		self.assertEqual(org.annual_revenue, 300000)

	def test_convert_to_deal_api_with_existing_records(self):
		"""Test convert_to_deal API with existing contact and organization parameters"""
		# Create existing contact
		existing_contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "API",
				"last_name": "Contact",
				"email_ids": [{"email_id": "apicontact@example.com", "is_primary": 1}],
			}
		).insert()

		# Create existing organization
		existing_org = frappe.get_doc(
			{
				"doctype": "CRM Organization",
				"organization_name": "API Org Ltd",
				"annual_revenue": 1500000,
			}
		).insert()

		# Create lead
		lead = create_lead(
			first_name="API",
			last_name="Lead",
			email="apilead@example.com",
			organization="Should Be Replaced",
		)

		# Convert lead using API with existing records
		deal_name = convert_to_deal(
			lead=lead.name,
			existing_contact=existing_contact.name,
			existing_organization=existing_org.name,
		)

		# Verify deal was created with existing records
		deal = frappe.get_doc("CRM Deal", deal_name)
		self.assertTrue(deal.name)

		# Verify existing contact is linked
		self.assertTrue(len(deal.contacts) > 0)
		self.assertEqual(deal.contacts[0].contact, existing_contact.name)

		# Verify existing organization is linked
		self.assertEqual(deal.organization, existing_org.name)

	def test_lead_fields_copied_to_deal(self):
		"""Test that relevant lead fields are copied to deal during conversion"""
		lead = create_lead(
			first_name="Copy",
			last_name="Test",
			email="copytest@example.com",
			mobile_no="+9999999999",
			organization="Copy Test Inc",
			website="https://copytest.com",
			annual_revenue=750000,
			job_title="CEO",
		)

		deal_name = lead.convert_to_deal()
		deal = frappe.get_doc("CRM Deal", deal_name)

		# Verify fields are copied
		self.assertEqual(deal.first_name, "Copy")
		self.assertEqual(deal.last_name, "Test")
		self.assertEqual(deal.website, "https://copytest.com")
		self.assertEqual(deal.annual_revenue, 750000)
		self.assertEqual(deal.job_title, "CEO")


def create_lead(**kwargs):
	"""Helper function to create a CRM Lead for testing"""
	data = {"doctype": "CRM Lead"}
	data.update(kwargs)
	return frappe.get_doc(data).insert()
