import frappe
from frappe.tests import IntegrationTestCase

EMAIL = "contact-details@example.com"
PHONE = "+4511111111"
MOBILE = "+4522222222"


class TestContactDetails(IntegrationTestCase):
	def tearDown(self):
		frappe.flags.in_import = False
		frappe.db.rollback()

	def make_contact(self, **fields):
		return frappe.get_doc({"doctype": "Contact", "first_name": "Contact Details", **fields}).insert(
			ignore_permissions=True
		)

	def test_new_contact_keeps_email_and_numbers_set_on_its_fields(self):
		contact = self.make_contact(email_id=EMAIL, phone=PHONE, mobile_no=MOBILE)
		contact.reload()

		self.assertEqual((contact.email_id, contact.phone, contact.mobile_no), (EMAIL, PHONE, MOBILE))
		self.assertEqual([(e.email_id, e.is_primary) for e in contact.email_ids], [(EMAIL, 1)])
		self.assertEqual(
			[(p.phone, p.is_primary_phone, p.is_primary_mobile_no) for p in contact.phone_nos],
			[(PHONE, 1, 0), (MOBILE, 0, 1)],
		)

	def test_same_phone_and_mobile_make_one_row(self):
		contact = self.make_contact(phone=PHONE, mobile_no=PHONE)

		self.assertEqual((contact.phone, contact.mobile_no), (PHONE, PHONE))
		self.assertEqual(
			[(p.phone, p.is_primary_phone, p.is_primary_mobile_no) for p in contact.phone_nos],
			[(PHONE, 1, 1)],
		)

	def test_child_rows_win_over_the_fields(self):
		contact = self.make_contact(
			email_id="other@example.com",
			mobile_no=MOBILE,
			email_ids=[{"email_id": EMAIL, "is_primary": 1}],
			phone_nos=[{"phone": PHONE, "is_primary_mobile_no": 1}],
		)

		self.assertEqual([e.email_id for e in contact.email_ids], [EMAIL])
		self.assertEqual([p.phone for p in contact.phone_nos], [PHONE])
		self.assertEqual((contact.email_id, contact.mobile_no), (EMAIL, PHONE))

	def test_removing_the_last_row_stays_removed(self):
		contact = self.make_contact(email_id=EMAIL, mobile_no=MOBILE)

		contact.email_ids = []
		contact.phone_nos = []
		contact.save(ignore_permissions=True)

		self.assertEqual((contact.email_id, contact.mobile_no), ("", ""))
		self.assertEqual((contact.email_ids, contact.phone_nos), ([], []))

	def test_import_fills_an_existing_contact_without_rows(self):
		contact = self.make_contact()

		contact.update({"email_id": EMAIL, "mobile_no": MOBILE})
		frappe.flags.in_import = True
		contact.save(ignore_permissions=True)

		self.assertEqual((contact.email_id, contact.mobile_no), (EMAIL, MOBILE))
		self.assertEqual([e.email_id for e in contact.email_ids], [EMAIL])
		self.assertEqual([p.phone for p in contact.phone_nos], [MOBILE])
