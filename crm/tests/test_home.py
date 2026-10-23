import frappe
from frappe.tests import IntegrationTestCase

from crm.api.home import LANDING_PAGE_KEY, set_landing_page


class TestLandingPage(IntegrationTestCase):
	def test_landing_page_is_a_user_default(self):
		set_landing_page("Deals")
		self.assertEqual(frappe.defaults.get_user_default(LANDING_PAGE_KEY), "Deals")

	def test_home_clears_the_landing_page(self):
		set_landing_page("Deals")
		set_landing_page("Home")
		self.assertIsNone(frappe.defaults.get_user_default(LANDING_PAGE_KEY))
