import frappe
from frappe.tests import IntegrationTestCase

from crm.api.home import (
	LANDING_PAGE_KEY,
	get_default_layout,
	get_layout,
	reset_default_layout,
	reset_layout,
	save_default_layout,
	save_layout,
	set_landing_page,
)
from crm.fcrm.doctype.crm_dashboard.home_layout import agent_default, manager_default, validate_layout


class TestLandingPage(IntegrationTestCase):
	def test_landing_page_is_a_user_default(self):
		set_landing_page("Deals")
		self.assertEqual(frappe.defaults.get_user_default(LANDING_PAGE_KEY), "Deals")

	def test_home_clears_the_landing_page(self):
		set_landing_page("Deals")
		set_landing_page("Home")
		self.assertIsNone(frappe.defaults.get_user_default(LANDING_PAGE_KEY))


AGENT = "home.agent@example.com"
MANAGER = "home.manager@example.com"


def make_user(email, *roles):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": email.split("@")[0], "send_welcome_email": 0}
		).insert(ignore_permissions=True)
	frappe.get_doc("User", email).add_roles(*roles)
	return email


def widget(name, x=0, y=0, w=10, h=8, **kwargs):
	return {"name": name, "layout": {"x": x, "y": y, "w": w, "h": h, "i": name}, **kwargs}


class TestHomeLayout(IntegrationTestCase):
	def setUp(self):
		make_user(AGENT, "Sales User")
		make_user(MANAGER, "Sales User", "Sales Manager")
		frappe.db.delete("CRM Dashboard", {"user": ["in", [AGENT, MANAGER]]})

	def tearDown(self):
		frappe.set_user("Administrator")

	def names(self, layout):
		return [item["name"] for item in layout]

	def test_agent_starts_from_the_agent_default(self):
		frappe.set_user(AGENT)
		home = get_layout()
		self.assertEqual(home["role"], "agent")
		self.assertTrue(home["is_default"])
		self.assertEqual(self.names(home["layout"]), self.names(agent_default()))

	def test_manager_starts_from_the_manager_default(self):
		frappe.set_user(MANAGER)
		home = get_layout()
		self.assertEqual(home["role"], "manager")
		self.assertEqual(self.names(home["layout"]), self.names(manager_default()))

	def test_getting_the_layout_creates_no_record(self):
		frappe.set_user(AGENT)
		get_layout()
		self.assertFalse(frappe.db.exists("CRM Dashboard", {"user": AGENT}))

	def test_saved_layout_is_one_record_per_user(self):
		frappe.set_user(AGENT)
		save_layout([widget("my_tasks")])
		save_layout([widget("replies_waiting", config={"doctype": "Deal"})])

		home = get_layout()
		self.assertFalse(home["is_default"])
		self.assertEqual(home["layout"][0]["config"], {"doctype": "Deal"})
		self.assertEqual(frappe.db.count("CRM Dashboard", {"user": AGENT}), 1)

	def test_saved_layout_is_kept_out_of_the_dashboard(self):
		frappe.set_user(AGENT)
		save_layout([widget("my_tasks")])
		name = frappe.db.get_value("CRM Dashboard", {"user": AGENT})
		self.assertTrue(name.startswith("Home - "))
		self.assertNotEqual(name, "Manager Dashboard")

	def test_reset_returns_to_the_role_default(self):
		frappe.set_user(AGENT)
		save_layout([widget("my_tasks")])
		home = reset_layout()
		self.assertTrue(home["is_default"])
		self.assertEqual(self.names(home["layout"]), self.names(agent_default()))
		self.assertFalse(frappe.db.exists("CRM Dashboard", {"user": AGENT}))

	def test_unknown_widget_is_rejected(self):
		frappe.set_user(AGENT)
		with self.assertRaises(frappe.ValidationError):
			save_layout([widget("sales_trend")])

	def test_duplicate_widget_is_rejected(self):
		frappe.set_user(AGENT)
		with self.assertRaises(frappe.ValidationError):
			save_layout([widget("my_tasks"), widget("my_tasks", y=8)])

	def test_manager_widgets_are_rejected_for_agents(self):
		frappe.set_user(AGENT)
		with self.assertRaises(frappe.ValidationError):
			save_layout([widget("team_overview", w=20)])

		frappe.set_user(MANAGER)
		self.assertEqual(
			self.names(save_layout([widget("team_overview", w=20)])["layout"]), ["team_overview"]
		)

	def test_manager_widgets_are_hidden_after_losing_the_role(self):
		frappe.set_user(MANAGER)
		save_layout([widget("team_overview", w=20), widget("my_tasks", y=8)])

		frappe.set_user("Administrator")
		frappe.get_doc("User", MANAGER).remove_roles("Sales Manager")

		frappe.set_user(MANAGER)
		self.assertEqual(self.names(get_layout()["layout"]), ["my_tasks"])

	def test_config_only_holds_the_doctype(self):
		frappe.set_user(AGENT)
		for config in ({"doctype": "Contact"}, {"doctype": "Lead", "limit": 5}, "Lead"):
			with self.assertRaises(frappe.ValidationError):
				save_layout([widget("replies_waiting", config=config)])
		with self.assertRaises(frappe.ValidationError):
			save_layout([widget("my_tasks", config={"doctype": "Lead"})])

		saved = save_layout([widget("replies_waiting")])["layout"][0]
		self.assertEqual(saved["config"], {"doctype": "Both"})

	def test_position_must_fit_the_grid(self):
		frappe.set_user(AGENT)
		for position in ({"x": 15, "w": 10}, {"w": 0}, {"x": -1}, {"h": "8"}):
			item = widget("my_tasks")
			item["layout"].update(position)
			with self.assertRaises(frappe.ValidationError):
				save_layout([item])

	def test_saved_items_drop_extra_keys(self):
		frappe.set_user(AGENT)
		item = widget("my_tasks", data=[1, 2])
		item["layout"]["moved"] = True
		self.assertEqual(
			save_layout([item])["layout"],
			[
				{
					"name": "my_tasks",
					"config": {},
					"layout": {"x": 0, "y": 0, "w": 10, "h": 8, "i": "my_tasks"},
				}
			],
		)


class TestHomeRoleDefaults(IntegrationTestCase):
	def setUp(self):
		make_user(AGENT, "Sales User")
		make_user(MANAGER, "Sales User", "Sales Manager")
		frappe.db.delete("CRM Dashboard", {"name": ["like", "Home - %"]})

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_admin_edits_the_agent_default(self):
		save_default_layout("agent", [widget("my_tasks")])
		frappe.set_user(AGENT)
		home = get_layout()
		self.assertTrue(home["is_default"])
		self.assertEqual([i["name"] for i in home["layout"]], ["my_tasks"])

	def test_admin_edits_the_manager_default(self):
		save_default_layout("manager", [widget("unassigned")])
		frappe.set_user(MANAGER)
		self.assertEqual([i["name"] for i in get_layout()["layout"]], ["unassigned"])

	def test_agent_default_rejects_manager_widgets(self):
		with self.assertRaises(frappe.ValidationError):
			save_default_layout("agent", [widget("unassigned")])

	def test_reset_default_returns_to_built_in(self):
		save_default_layout("agent", [widget("my_tasks")])
		default = reset_default_layout("agent")
		self.assertTrue(default["is_default"])
		self.assertEqual(default["layout"], agent_default())

	def test_only_system_manager_edits_defaults(self):
		frappe.set_user(MANAGER)
		with self.assertRaises(frappe.PermissionError):
			get_default_layout("manager")
		with self.assertRaises(frappe.PermissionError):
			save_default_layout("manager", [widget("unassigned")])

	def test_unknown_role_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			get_default_layout("owner")

	def test_built_in_defaults_are_valid(self):
		self.assertEqual(validate_layout(agent_default(), "agent"), agent_default())
		self.assertEqual(validate_layout(manager_default(), "manager"), manager_default())
