import frappe
from frappe.desk.form.assign_to import add as assign
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime, nowdate

from crm.api.home import (
	LANDING_PAGE_KEY,
	get_counts,
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

	def test_built_in_defaults_do_not_overlap(self):
		for default, role in ((agent_default, "agent"), (manager_default, "manager")):
			layout = validate_layout(default(), role)
			cells = [
				(x, y)
				for item in layout
				for x in range(item["layout"]["x"], item["layout"]["x"] + item["layout"]["w"])
				for y in range(item["layout"]["y"], item["layout"]["y"] + item["layout"]["h"])
			]
			self.assertEqual(len(cells), len(set(cells)), role)

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


class TestHomeCounts(IntegrationTestCase):
	def setUp(self):
		make_user(AGENT, "Sales User")
		make_user(MANAGER, "Sales User", "Sales Manager")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def counts(self):
		frappe.set_user(AGENT)
		counts = get_counts()
		frappe.set_user("Administrator")
		return counts

	def test_replies_waiting_counts_my_leads_and_deals(self):
		make_lead(lead_owner=AGENT, awaiting_reply_since=now_datetime())
		make_lead(lead_owner=AGENT)
		make_lead(lead_owner=MANAGER, awaiting_reply_since=now_datetime())
		make_lead(lead_owner=AGENT, awaiting_reply_since=now_datetime(), converted=1)
		make_deal(deal_owner=AGENT, awaiting_reply_since=now_datetime())
		self.assertEqual(self.counts()["replies_waiting"], 2)

	def test_assigned_records_count_as_mine(self):
		lead = make_lead(lead_owner=MANAGER, awaiting_reply_since=now_datetime())
		assign({"assign_to": [AGENT], "doctype": "CRM Lead", "name": lead})
		self.assertEqual(self.counts()["replies_waiting"], 1)

	def test_new_leads_are_my_open_leads(self):
		open_status = frappe.get_all("CRM Lead Status", filters={"type": "Open"}, pluck="name")[0]
		other_status = frappe.get_all("CRM Lead Status", filters={"type": ["!=", "Open"]}, pluck="name")[0]
		make_lead(lead_owner=AGENT, status=open_status)
		make_lead(lead_owner=AGENT, status=other_status)
		make_lead(lead_owner=MANAGER, status=open_status)
		self.assertEqual(self.counts()["new_leads"], 1)

	def test_follow_ups_due_are_my_open_linked_tasks_due_by_today(self):
		lead = make_lead(lead_owner=AGENT)
		linked = {"reference_doctype": "CRM Lead", "reference_docname": lead, "assigned_to": AGENT}
		make_task(add_days(now_datetime(), -2), **linked)
		make_task(nowdate(), all_day=1, **linked)
		make_task(add_days(now_datetime(), 7), **linked)
		make_task(add_days(now_datetime(), -2), status="Done", **linked)
		make_task(add_days(now_datetime(), -2), assigned_to=AGENT)
		make_task(add_days(now_datetime(), -2), **{**linked, "assigned_to": MANAGER})
		self.assertEqual(self.counts()["follow_ups_due"], 2)


def make_lead(**kwargs) -> str:
	return frappe.get_doc({"doctype": "CRM Lead", "first_name": "Home", **kwargs}).insert().name


def make_deal(**kwargs) -> str:
	deal = frappe.get_doc({"doctype": "CRM Deal", **kwargs})
	deal.flags.ignore_mandatory = True
	return deal.insert().name


def make_task(due_date, **kwargs):
	return frappe.get_doc(
		{"doctype": "CRM Task", "title": "Follow up", "due_date": due_date, **kwargs}
	).insert()
