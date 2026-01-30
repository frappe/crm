from frappe.tests import UnitTestCase

from crm.utils import are_same_phone_number, seconds_to_duration


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
