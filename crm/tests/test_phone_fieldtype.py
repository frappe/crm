import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field
from frappe.tests import IntegrationTestCase

from crm.api.doc import get_filterable_fields, get_group_by_fields

PHONE_FIELD = "custom_alt_phone"


class TestPhoneFieldtype(IntegrationTestCase):
	"""Custom fields of the native Phone fieldtype can be filtered and grouped by
	in list views (frappe/crm#2901)."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not frappe.db.exists("Custom Field", {"dt": "CRM Lead", "fieldname": PHONE_FIELD}):
			create_custom_field(
				"CRM Lead",
				{"fieldname": PHONE_FIELD, "label": "Alt Phone", "fieldtype": "Phone"},
			)
		frappe.clear_cache(doctype="CRM Lead")

	def test_phone_field_is_filterable(self):
		fields = [f["fieldname"] for f in get_filterable_fields("CRM Lead")]
		self.assertIn(PHONE_FIELD, fields)

	def test_phone_field_is_groupable(self):
		fields = [f["fieldname"] for f in get_group_by_fields("CRM Lead")]
		self.assertIn(PHONE_FIELD, fields)
