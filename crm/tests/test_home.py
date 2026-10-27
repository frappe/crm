import json
from contextlib import contextmanager

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.desk.form.assign_to import add as assign
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime, nowdate

from crm.api.home import (
	LANDING_PAGE_KEY,
	get_counts,
	get_default_layout,
	get_layout,
	get_widget_columns,
	reset_default_layout,
	reset_layout,
	save_default_layout,
	save_layout,
	set_landing_page,
)
from crm.fcrm.doctype.crm_dashboard.home_layout import (
	WIDGETS,
	agent_default,
	manager_default,
	validate_layout,
)


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


def reply_columns(*extra, **column):
	keys = ("title", "awaiting_reply_since", *extra)
	return [{"key": key, **(column if key == keys[-1] else {})} for key in keys]


@contextmanager
def unreadable(doctype, fieldname):
	"""No role reads permlevel 1 on CRM records."""
	make_property_setter(doctype, fieldname, "permlevel", 1, "Int", validate_fields_for_doctype=False)
	try:
		yield
	finally:
		frappe.db.delete("Property Setter", {"doc_type": doctype, "field_name": fieldname})
		frappe.clear_cache(doctype=doctype)


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
		save_layout([widget("my_tasks", w=20)])
		save_layout([widget("replies_waiting", config={"doctype": "Deal"})])

		home = get_layout()
		self.assertFalse(home["is_default"])
		self.assertEqual(home["layout"][0]["config"], {"doctype": "Deal"})
		self.assertEqual(frappe.db.count("CRM Dashboard", {"user": AGENT}), 1)

	def test_saved_layout_is_kept_out_of_the_dashboard(self):
		frappe.set_user(AGENT)
		save_layout([widget("my_tasks", w=20)])
		name = frappe.db.get_value("CRM Dashboard", {"user": AGENT})
		self.assertTrue(name.startswith("Home - "))
		self.assertNotEqual(name, "Manager Dashboard")

	def test_reset_returns_to_the_role_default(self):
		frappe.set_user(AGENT)
		save_layout([widget("my_tasks", w=20)])
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
			save_layout([widget("my_tasks", w=20), widget("my_tasks", w=20, y=8)])

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
		save_layout([widget("team_overview", w=20), widget("my_tasks", w=20, y=8)])

		frappe.set_user("Administrator")
		frappe.get_doc("User", MANAGER).remove_roles("Sales Manager")

		frappe.set_user(MANAGER)
		self.assertEqual(self.names(get_layout()["layout"]), ["my_tasks"])

	def test_config_holds_the_doctype_and_columns(self):
		frappe.set_user(AGENT)
		for config in ({"doctype": "Contact"}, {"doctype": "Lead", "limit": 5}, "Lead"):
			with self.assertRaises(frappe.ValidationError):
				save_layout([widget("replies_waiting", config=config)])
		with self.assertRaises(frappe.ValidationError):
			save_layout([widget("my_tasks", w=20, config={"doctype": "Lead"})])

		saved = save_layout([widget("replies_waiting")])["layout"][0]
		self.assertEqual(saved["config"], {"doctype": "Both"})

	def test_position_must_fit_the_grid(self):
		frappe.set_user(AGENT)
		for position in ({"x": 15, "w": 10}, {"w": 0}, {"x": -1}, {"h": "8"}):
			item = widget("my_tasks", w=20)
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

	def test_task_widgets_span_the_full_width(self):
		frappe.set_user(MANAGER)
		for name in ("follow_ups_due", "upcoming_follow_ups", "my_tasks", "team_overdue_follow_ups"):
			with self.assertRaises(frappe.ValidationError):
				save_layout([widget(name, x=10, w=10)])
		self.assertEqual(save_layout([widget("team_overview")])["layout"][0]["layout"]["w"], 10)

	def test_narrow_task_widget_saved_earlier_is_widened(self):
		frappe.set_user(AGENT)
		save_layout([widget("replies_waiting")])
		name = frappe.db.get_value("CRM Dashboard", {"user": AGENT})
		old = [widget("replies_waiting", config={"doctype": "Both"}), widget("my_tasks", x=10, config={})]
		frappe.db.set_value("CRM Dashboard", name, "layout", json.dumps(old))

		position = get_layout()["layout"][1]["layout"]
		self.assertEqual((position["x"], position["w"]), (0, 20))

	def test_built_in_defaults_respect_min_widths(self):
		for layout in (agent_default(), manager_default()):
			for item in layout:
				self.assertGreaterEqual(item["layout"]["w"], WIDGETS[item["name"]].min_w, item["name"])

	def test_saved_items_drop_extra_keys(self):
		frappe.set_user(AGENT)
		item = widget("my_tasks", w=20, data=[1, 2])
		item["layout"]["moved"] = True
		self.assertEqual(
			save_layout([item])["layout"],
			[
				{
					"name": "my_tasks",
					"config": {},
					"layout": {"x": 0, "y": 0, "w": 20, "h": 8, "i": "my_tasks"},
				}
			],
		)


class TestHomeColumns(IntegrationTestCase):
	def setUp(self):
		make_user(AGENT, "Sales User")
		frappe.db.delete("CRM Dashboard", {"user": AGENT})
		frappe.set_user(AGENT)

	def tearDown(self):
		frappe.set_user("Administrator")

	def save(self, columns, doctype="Both", name="replies_waiting", **layout):
		config = {"doctype": doctype, "columns": columns} if doctype else {"columns": columns}
		return save_layout([widget(name, config=config, **layout)])["layout"][0]["config"]

	def assertRejected(self, columns, doctype="Both", name="replies_waiting", **layout):
		with self.assertRaises(frappe.ValidationError):
			self.save(columns, doctype, name, **layout)

	def test_lead_and_deal_widgets_offer_their_own_fields(self):
		self.assertEqual(self.save(reply_columns("lead_score"), "Lead")["columns"][-1], {"key": "lead_score"})
		self.assertRejected(reply_columns("deal_value"), "Lead")
		self.assertEqual(self.save(reply_columns("deal_value"), "Deal")["columns"][-1], {"key": "deal_value"})
		self.assertRejected(reply_columns("lead_score"), "Deal")

	def test_both_offers_shared_fields_and_the_owner_alias(self):
		self.assertEqual(self.save(reply_columns("owner"))["columns"][-1], {"key": "owner"})
		self.save(reply_columns("territory"))
		for key in ("lead_owner", "deal_value", "organization"):
			self.assertRejected(reply_columns(key))

		available = {field["fieldname"] for field in get_widget_columns("replies_waiting")["fields"]}
		self.assertIn("owner", available)
		self.assertIn("territory", available)
		self.assertNotIn("lead_owner", available)
		self.assertNotIn("organization", available)

	def test_unknown_hidden_and_non_value_fields_are_rejected(self):
		for key in ("not_a_field", "image", "_assign", "naming_series_break", "lost_notes"):
			self.assertRejected(reply_columns(key), "Lead")

	def test_unreadable_field_is_rejected(self):
		with unreadable("CRM Lead", "lead_score"):
			self.assertRejected(reply_columns("lead_score"), "Lead")
			available = {
				field["fieldname"] for field in get_widget_columns("replies_waiting", "Lead")["fields"]
			}
			self.assertNotIn("lead_score", available)

	def test_unreadable_field_is_dropped_from_a_saved_layout(self):
		self.save(reply_columns("lead_score"), "Lead")
		with unreadable("CRM Lead", "lead_score"):
			columns = get_layout()["layout"][0]["config"]["columns"]
		self.assertEqual([column["key"] for column in columns], ["title", "awaiting_reply_since"])

	def test_locked_columns_cannot_be_removed(self):
		self.assertRejected([{"key": "title"}, {"key": "status"}])
		self.assertRejected(
			[{"key": "title"}, {"key": "reference_title"}, {"key": "due_date"}],
			name="follow_ups_due",
			w=20,
		)
		locked = get_widget_columns("follow_ups_due")["locked"]
		self.assertEqual(list(locked), ["title", "due_date", "actions"])

	def test_built_in_columns_can_be_reordered_or_removed(self):
		columns = [{"key": "awaiting_reply_since"}, {"key": "title", "label": "Who"}]
		self.assertEqual(self.save(columns)["columns"], columns)

	def test_task_widgets_offer_task_fields(self):
		columns = [{"key": key} for key in ("status", "title", "due_date", "start_date")]
		self.assertEqual(self.save(columns, None, "my_tasks", w=20)["columns"], columns)
		self.assertRejected([*columns, {"key": "lead_score"}], None, "my_tasks", w=20)

	def test_team_overview_has_no_columns(self):
		frappe.set_user("Administrator")
		with self.assertRaises(frappe.ValidationError):
			save_layout([widget("team_overview", config={"columns": [{"key": "user"}]})])

	def test_column_label_and_width_are_checked(self):
		self.save(reply_columns("territory", label="Region", width="8rem"))
		self.save(reply_columns("territory", width="minmax(0,2fr)"))
		for column in ({"width": "8rem;color:red"}, {"label": "x" * 200}, {"label": 5}, {"align": "right"}):
			self.assertRejected(reply_columns("territory", **column))

	def test_duplicate_column_is_rejected(self):
		self.assertRejected(reply_columns("territory", "territory"))


class TestHomeRoleDefaults(IntegrationTestCase):
	def setUp(self):
		make_user(AGENT, "Sales User")
		make_user(MANAGER, "Sales User", "Sales Manager")
		frappe.db.delete("CRM Dashboard", {"name": ["like", "Home - %"]})

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_admin_edits_the_agent_default(self):
		save_default_layout("agent", [widget("my_tasks", w=20)])
		frappe.set_user(AGENT)
		home = get_layout()
		self.assertTrue(home["is_default"])
		self.assertEqual([i["name"] for i in home["layout"]], ["my_tasks"])

	def test_admin_edits_the_manager_default(self):
		save_default_layout("manager", [widget("unassigned")])
		frappe.set_user(MANAGER)
		self.assertEqual([i["name"] for i in get_layout()["layout"]], ["unassigned"])

	def test_role_default_carries_columns(self):
		columns = [{"key": "title"}, {"key": "awaiting_reply_since"}, {"key": "owner", "label": "Rep"}]
		save_default_layout("agent", [widget("replies_waiting", config={"columns": columns})])
		frappe.set_user(AGENT)
		self.assertEqual(get_layout()["layout"][0]["config"], {"doctype": "Both", "columns": columns})

	def test_agent_default_rejects_manager_widgets(self):
		with self.assertRaises(frappe.ValidationError):
			save_default_layout("agent", [widget("unassigned")])

	def test_reset_default_returns_to_built_in(self):
		save_default_layout("agent", [widget("my_tasks", w=20)])
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
