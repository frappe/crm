import frappe
from frappe.tests import IntegrationTestCase

from crm.api.contact import get_linked_deals
from crm.permissions.test_org_hierarchy import make_user


class TestContactLinkedDeals(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		make_user("rep1-45892@example.com", roles=["Sales User"])
		make_user("rep2-45892@example.com", roles=["Sales User"])

	def setUp(self):
		frappe.db.savepoint("test_contact_deals")
		self.contact = frappe.get_doc({"doctype": "Contact", "first_name": "Contact Deals"}).insert(
			ignore_permissions=True
		)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback(save_point="test_contact_deals")

	def test_lists_the_deals_that_name_the_contact(self):
		own = make_deal("rep1-45892@example.com", self.contact.name)
		other = make_deal("rep2-45892@example.com", self.contact.name)
		make_deal("rep1-45892@example.com", None)

		deals = get_linked_deals(self.contact.name)

		self.assertEqual({deal.name for deal in deals}, {own.name, other.name})
		self.assertEqual(next(deal for deal in deals if deal.name == own.name).deal_owner_name, "rep1-45892")

	def test_leaves_out_the_deals_the_user_cannot_read(self):
		own = make_deal("rep1-45892@example.com", self.contact.name)
		make_deal("rep2-45892@example.com", self.contact.name)

		frappe.set_user("rep1-45892@example.com")
		deals = get_linked_deals(self.contact.name)

		self.assertEqual([deal.name for deal in deals], [own.name])


def make_deal(owner_email, contact):
	doc = frappe.get_doc({"doctype": "CRM Deal", "deal_owner": owner_email, "organization": "Test Org"})
	if contact:
		doc.append("contacts", {"contact": contact})
	doc.flags.ignore_mandatory = True
	doc.flags.ignore_links = True
	return doc.insert(ignore_permissions=True)
