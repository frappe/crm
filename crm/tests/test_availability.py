import frappe

from crm.install import add_default_availability_statuses
from crm.tests import CRMTestCase

USERS = ("avail-a@example.com", "avail-b@example.com")


class TestAvailability(CRMTestCase):
	def setUp(self):
		add_default_availability_statuses()
		frappe.db.set_value("CRM Availability Status", {"name": ["is", "set"]}, "enabled", 1)
		for email in USERS:
			if not frappe.db.exists("User", email):
				user = frappe.get_doc(
					{
						"doctype": "User",
						"email": email,
						"first_name": email.split("@")[0],
						"send_welcome_email": 0,
					}
				).insert(ignore_permissions=True)
				user.add_roles("Sales User")
			# on frappe v15 the assignment email is sent synchronously in tests and commits
			frappe.db.set_value("Notification Settings", email, "enable_email_notifications", 0)
		frappe.db.delete("Assignment Rule", {"document_type": "CRM Lead"})
		self.rule = frappe.get_doc(
			{
				"doctype": "Assignment Rule",
				"name": "Availability Test",
				"document_type": "CRM Lead",
				"assign_condition": "status == 'New'",
				"rule": "Round Robin",
				"users": [{"user": user} for user in USERS],
				"assignment_days": [
					{"day": day}
					for day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
				],
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.db.rollback()

	def set_status(self, user, status):
		doc = frappe.get_doc("User", user)
		doc.crm_availability = status
		doc.save(ignore_permissions=True)

	def assigned_to(self):
		lead = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Availability", "status": "New"}).insert()
		return frappe.get_all(
			"ToDo",
			{"reference_type": "CRM Lead", "reference_name": lead.name, "status": "Open"},
			pluck="allocated_to",
		)

	def test_status_change_is_stamped(self):
		self.set_status(USERS[0], "Away")
		user = frappe.db.get_value(
			"User", USERS[0], ["crm_availability_changed_on", "crm_availability_changed_by"], as_dict=True
		)
		self.assertTrue(user.crm_availability_changed_on)
		self.assertEqual(user.crm_availability_changed_by, frappe.session.user)

	def test_disabled_status_is_rejected(self):
		self.set_status(USERS[0], None)
		frappe.db.set_value("CRM Availability Status", "Away", "enabled", 0)
		self.assertRaises(frappe.ValidationError, self.set_status, USERS[0], "Away")

	def test_active_user_is_preferred(self):
		self.set_status(USERS[0], "Away")
		self.set_status(USERS[1], None)
		self.assertEqual(self.assigned_to(), [USERS[1]])
		self.assertEqual(self.assigned_to(), [USERS[1]])

	def test_away_user_is_preferred_over_unavailable(self):
		self.set_status(USERS[0], "Unavailable")
		self.set_status(USERS[1], "Away")
		self.assertEqual(self.assigned_to(), [USERS[1]])

	def test_everyone_unavailable_still_assigns(self):
		self.set_status(USERS[0], "Unavailable")
		self.set_status(USERS[1], "Unavailable")
		self.assertEqual(len(self.assigned_to()), 1)
