import frappe
from frappe.desk.doctype.form_layout.form_layout import get_layouts, opens_in_dialog
from frappe.tests import IntegrationTestCase

LAYOUT_DOCTYPES = (
	"CRM Lead",
	"CRM Deal",
	"CRM Organization",
	"CRM Task",
	"FCRM Note",
	"CRM Call Log",
)

# Settings records, SLA (required child tables) and records only an editor or the server makes:
# asked on frappe/frappe#45885.
LEFT_OUT = {
	"CRM Global Settings",
	"CRM Service Level Agreement",
	"CRM Dashboard",
	"CRM Fields Layout",
	"CRM Notification",
}


class TestQuickEntry(IntegrationTestCase):
	def test_every_creatable_crm_doctype_opens_in_dialog(self):
		full_page = [
			dt for dt in creatable_crm_doctypes() if not opens_in_dialog(dt, quick_entry_layouts(dt))
		]
		self.assertEqual(full_page, [])

	def test_layout_doctypes_have_a_default_quick_entry_layout(self):
		for dt in LAYOUT_DOCTYPES:
			with self.subTest(dt=dt):
				defaults = [layout for layout in quick_entry_layouts(dt) if not layout["condition"]]
				self.assertEqual(len(defaults), 1)
				self.assertTrue(defaults[0]["layout"])

	def test_deal_quick_entry_has_plain_organization_and_contact_links(self):
		fields = quick_entry_fields("CRM Deal")
		self.assertIn("organization", fields)
		self.assertIn("contact", fields)
		self.assertNotIn("organization_name", fields)
		self.assertNotIn("first_name", fields)

	def test_create_dialogs_hold_no_website_preview(self):
		for dt in LAYOUT_DOCTYPES:
			with self.subTest(dt=dt):
				meta = frappe.get_meta(dt)
				previews = [
					fieldname
					for fieldname in quick_entry_fields(dt)
					if (field := meta.get_field(fieldname))
					and field.fieldtype in ("HTML", "Attach Image", "Image")
				]
				self.assertEqual(previews, [])


def creatable_crm_doctypes() -> list[str]:
	"""CRM doctypes whose list shows Create: not a child table, a Single, `in_create` or read only."""
	doctypes = frappe.get_all(
		"DocType",
		filters={
			"module": ("in", frappe.get_module_list("crm")),
			"istable": 0,
			"issingle": 0,
			"in_create": 0,
			"read_only": 0,
		},
		pluck="name",
	)
	return sorted(dt for dt in doctypes if dt not in LEFT_OUT and any_role_can_create(dt))


def any_role_can_create(dt: str) -> bool:
	return any(perm.create for perm in frappe.get_meta(dt).permissions)


def quick_entry_layouts(dt: str) -> list[dict]:
	return get_layouts(dt, "Quick Entry")


def quick_entry_fields(dt: str) -> list[str]:
	default = next((layout for layout in quick_entry_layouts(dt) if not layout["condition"]), None)
	assert default, f"{dt} has no default Quick Entry layout"
	return [
		fieldname
		for tab in default["layout"]
		for section in tab["sections"]
		for column in section["columns"]
		for fieldname in column["fields"]
	]
