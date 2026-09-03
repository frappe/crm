# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

"""CRM's shipped desk v2 navigation: one Rail record and four addressed Sidebars.

These are fixture tests. CRM ships no navigation code at all -- the rows arrive as JSON at
`bench migrate` and the framework resolves them -- so what there is to get wrong is the
content of those rows: a rail item naming a sidebar nobody ships, a row pointing at a
doctype this site does not have, or two rows claiming one key. Each of those resolves to a
quietly shorter list rather than to an error, which is why they are asserted here.

Every test runs as a `Desk User` rather than as Administrator. The permission filter
short-circuits for an administrator (`navigation_filter`), so an Administrator suite would
pass against a rail that is not being filtered at all.
"""

import frappe
from frappe.shell.navigation import resolve_navigation
from frappe.tests import IntegrationTestCase

RAIL = ("leads", "deals", "contacts", "organizations", "tasks", "notes")

# The four primary doctypes that open a sidebar, by the scrubbed address boot files them
# under -- which is also the string the rail item of type `Sidebar` carries in `link_to`.
SIDEBARS = {
	"doctype_crm_lead": ("leads", "leads-configure", "lead-statuses", "lead-sources", "lost-reasons"),
	"doctype_crm_deal": ("deals", "deals-configure", "deal-statuses", "products", "territories"),
	"doctype_contact": ("contacts", "call-logs"),
	"doctype_crm_organization": (
		"organizations",
		"organizations-configure",
		"industries",
		"territories",
	),
}

# The two rail items that open no sidebar. Charter point 1 makes independent a first-class
# state and nothing else on this rail exercises it.
INDEPENDENT = ("tasks", "notes")


class TestCRMNavigation(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.user = make_desk_user("crm.navigation.test@example.com")

	def setUp(self):
		frappe.set_user(self.user)
		# `IntegrationTestCase` rolls back once per CLASS, so a layer written by one test is still
		# there for the next one -- and every test here reads the same rail. Cleared per test, or
		# the arrangement tests below silently rewrite what the others assert.
		self.addCleanup(frappe.set_user, "Administrator")
		self.addCleanup(self.drop_layer, self.user)

	def test_rail_is_the_six_authored_items(self):
		"""The shipped rail replaces the derived one, which is every CRM doctype in the site."""
		rail = resolve_navigation("crm")["rail"]

		self.assertEqual(tuple(item["key"] for item in rail), RAIL)

	def test_every_sidebar_resolves_with_its_rows(self):
		sidebars = resolve_navigation("crm")["sidebars"]

		self.assertEqual(
			{address: tuple(row["key"] for row in rows) for address, rows in sidebars.items()},
			SIDEBARS,
		)

	def test_a_linked_item_names_a_sidebar_this_app_ships(self):
		"""A typo in `link_to` costs the item its panel and nothing else, so nothing reports it.

		Read off the **shipped rows**, not the resolved payload. `Sidebar` declares the
		`Derived From Children` permission rule, so an item naming an address that resolves to no
		rows is dropped by the server's own cascade -- silently, and correctly, because that is
		also what an emptied sidebar has to do. Asserting against the resolved list would
		therefore be asserting that the cascade works, which is frappe's test and not this one.
		"""
		linked = [row for row in shipped("Rail", "crm") if row.item_type == "Sidebar"]
		addresses = set(frappe.get_all("Sidebar", filters={"app": "crm", "standard": 1}, pluck="name"))

		self.assertEqual({row.link_to for row in linked}, set(SIDEBARS))
		for row in linked:
			self.assertIn(row.link_to, addresses, row.key)

	def test_the_independent_items_open_nothing(self):
		rail = {item["key"]: item for item in resolve_navigation("crm")["rail"]}

		for key in INDEPENDENT:
			self.assertEqual(rail[key]["item_type"], "DocType")

	def test_the_containers_are_the_rail_and_its_four_sidebars(self):
		"""What `every_container()` finds, which four tests below iterate and would otherwise
		pass over in silence if the fixtures had not been imported at all."""
		self.assertEqual(
			set(every_container()),
			{("Rail", "crm")} | {("Sidebar", address) for address in SIDEBARS},
		)

	def test_every_destination_is_a_doctype_this_site_has(self):
		"""Read off the shipped rows rather than the resolved payload, which has already dropped
		any row it could not place.

		A typo cannot get this far: `link_to` is a Dynamic Link, so `_validate_links` refuses the
		row at import with `Could not find Row #N: Link To` -- checked, not assumed. What is left
		for this to catch is a doctype removed *after* the rows were imported, which arrives as a
		quietly shorter sidebar and nothing else.
		"""
		for container, address in every_container():
			for row in shipped(container, address):
				if row.item_type == "DocType":
					self.assertTrue(frappe.db.exists("DocType", row.link_to), f"{address}/{row.key}")

	def test_crm_territory_is_listed_in_both_the_panels_it_belongs_to(self):
		"""The replacement for the guard that said the opposite. See the note.

		CRM used to ship each destination exactly once, because an address resolved to exactly
		one panel: the deepest cover won and equal covers tie-broke on rail order, so clicking
		Territories in the Organizations panel moved the reader to Deals. `CRM Territory` was
		removed from Organizations rather than the behaviour being fixed, and a test guarded
		that removal.

		The reader now keeps the panel they are in, so a destination may be listed in as many
		panels as it belongs in. This asserts the restored row rather than merely allowing it,
		so the thinning is not quietly redone by someone reading the old convention.

		Read off the shipped rows: a destination the reader cannot open is gone from the
		resolved payload, so the row could hide behind a permission rather than be reported.
		"""
		panels = set()

		for container, address in every_container():
			# The rail is not one of the panels this is about, and it carries `DocType` rows of
			# its own -- Tasks and Notes.
			if container != "Sidebar":
				continue
			for row in shipped(container, address):
				if (row.link_doctype, row.link_to) == ("DocType", "CRM Territory"):
					panels.add(address)

		self.assertEqual(panels, {"doctype_crm_deal", "doctype_crm_organization"})

	def test_keys_are_unique_within_each_container(self):
		"""Every site and user edit is filed against a key, so two rows sharing one collide."""
		for container, address in every_container():
			keys = [row.key for row in shipped(container, address)]
			self.assertEqual(len(keys), len(set(keys)), address)

	def test_no_section_is_shipped_over_nothing(self):
		"""A heading with no rows under it is dropped by the cascade at read time, so shipping one
		would mean shipping a row that can never render. Left out at authoring instead -- and read
		here off the shipped rows, since the cascade would have hidden it either way."""
		for container, address in every_container():
			rows = shipped(container, address)
			parents = {row.parent_key for row in rows}
			for row in rows:
				if row.item_type == "Section":
					self.assertIn(row.key, parents, f"{address}/{row.key}")

	def test_every_parent_key_names_a_section_beside_it(self):
		"""A row filed under a heading that is not there loses its nesting silently: the resolver
		promotes an orphan to the top level rather than dropping it."""
		for container, address in every_container():
			rows = shipped(container, address)
			sections = {row.key for row in rows if row.item_type == "Section"}
			for row in rows:
				if row.parent_key:
					self.assertIn(row.parent_key, sections, f"{address}/{row.key}")

	def test_a_configure_section_drops_when_its_doctypes_are_unreadable(self):
		"""The section cascade, on the first shipped section on this branch.

		A person who cannot read the three lead-configuration doctypes is left with a heading
		over nothing, so the section goes with them -- and the sidebar keeps its own list.
		"""
		unreadable = ("CRM Lead Status", "CRM Lead Source", "CRM Lost Reason")
		with self.patch_readable(exclude=unreadable):
			rows = resolve_navigation("crm")["sidebars"]["doctype_crm_lead"]

		self.assertEqual(tuple(row["key"] for row in rows), ("leads",))

	def test_a_linked_item_goes_when_its_whole_sidebar_goes(self):
		"""`Derived From Children`, across containers: no rows left, no rail item either."""
		with self.patch_readable(exclude=("Contact", "CRM Call Log")):
			navigation = resolve_navigation("crm")

		self.assertNotIn("doctype_contact", navigation["sidebars"])
		self.assertNotIn("contacts", [item["key"] for item in navigation["rail"]])

	def test_one_persons_arrangement_is_theirs_alone(self):
		"""The per-user overlay over rows an app SHIPS, which is new here.

		Every rail the framework's own suites arrange is derived or built in the test, so this is
		the first arrangement filed against authored keys. What is stored is the difference from
		the shipped list -- three rows out of six for the three changes below -- which is
		#42229's sparse move-list doing the work a stored copy of the whole list could not.
		"""
		from frappe.shell.arrangement import get_arrangement, save_arrangement

		desired = [dict(item) for item in get_arrangement("Rail", "crm")]
		desired.insert(0, desired.pop())  # notes to the top
		by_key = {item["key"]: item for item in desired}
		by_key["leads"]["label"] = "My Leads"
		by_key["deals"]["hidden"] = 1

		mine = save_arrangement("Rail", "crm", desired)["rail"]

		self.assertEqual(
			[(item["key"], item["label"]) for item in mine],
			[
				("notes", "Notes"),
				("leads", "My Leads"),
				("contacts", "Contacts"),
				("organizations", "Organizations"),
				("tasks", "Tasks"),
			],
		)
		self.assertEqual(self.stored_layer_keys(), {"notes", "leads", "deals"})

		frappe.set_user("Administrator")
		self.assertEqual(
			tuple(item["key"] for item in resolve_navigation("crm")["rail"]),
			RAIL,
			"another person's rail is untouched",
		)

	def test_an_arrangement_survives_the_app_shipping_the_rail_again(self):
		"""#42229's promise: a delta is filed against a frozen key, not against a position.

		Re-importing the fixture is what an app upgrade does to these rows, and it replaces the
		record wholesale. The person's layer is a separate record naming keys, so it still
		resolves -- which is the whole reason a key is authored and frozen rather than computed.
		"""
		from frappe.shell.arrangement import get_arrangement, save_arrangement

		desired = [dict(item) for item in get_arrangement("Rail", "crm")]
		desired.insert(0, desired.pop())
		save_arrangement("Rail", "crm", desired)

		frappe.set_user("Administrator")
		reimport_shipped_rail()
		frappe.set_user(self.user)

		mine = resolve_navigation("crm")["rail"]

		self.assertEqual(mine[0]["key"], "notes")

	def drop_layer(self, user: str):
		"""Named rather than read off the session, which a test may have changed by then."""
		for name in frappe.get_all("Rail", filters={"app": "crm", "user": user, "standard": 0}, pluck="name"):
			frappe.delete_doc("Rail", name, force=True, ignore_permissions=True)

	def stored_layer_keys(self) -> set[str]:
		layer = frappe.db.get_value("Rail", {"app": "crm", "user": frappe.session.user, "standard": 0})

		return set(
			frappe.get_all(
				"Navigation Item",
				filters={"parenttype": "Rail", "parent": layer},
				pluck="key",
			)
		)

	def patch_readable(self, exclude: tuple[str, ...]):
		"""Take some doctypes away from this user, as the filter reads readability.

		Patched rather than acted out with `DocPerm` rows, because the filter reads one cached
		set per request (`get_readable_doctypes`) and taking a role away would have to reach
		every doctype that role grants rather than the three the test is about.
		"""
		from unittest.mock import patch

		from frappe.shell.doctypes import get_readable_doctypes

		readable = get_readable_doctypes()

		# `shell.doctypes` and not `shell.navigation_filter`, which imports the name inside the
		# property that reads it, so the filter's own module never holds it as an attribute.
		return patch(
			"frappe.shell.doctypes.get_readable_doctypes",
			return_value={name for name in readable if name not in exclude},
		)


def every_container() -> list[tuple[str, str]]:
	"""Every standard record CRM ships, as `(doctype, name)`."""
	return [("Rail", "crm")] + [
		("Sidebar", name)
		for name in frappe.get_all("Sidebar", filters={"app": "crm", "standard": 1}, pluck="name")
	]


def shipped(container: str, address: str) -> list:
	"""The rows as authored, before the resolver has filtered or cascaded anything away.

	The distinction matters for every fixture assertion above: `resolve_navigation` drops a row
	naming a doctype that is gone, a heading over nothing and a linked item whose sidebar
	emptied. Read against its output, a test for those is asserting that the resolver works.
	"""
	return frappe.get_all(
		"Navigation Item",
		filters={
			"parenttype": container,
			"parent": address,
			"parentfield": "items" if container == "Rail" else "navigation_items",
		},
		fields=["key", "parent_key", "item_type", "link_doctype", "link_to"],
		order_by="idx asc",
	)


def reimport_shipped_rail():
	"""Re-import `crm/rail/crm/crm.json`, which is what an app upgrade does to that record."""
	import os

	from frappe.modules.import_file import import_file_by_path

	path = os.path.join(frappe.get_app_path("crm"), "rail", "crm", "crm.json")
	import_file_by_path(path, force=True, ignore_version=True)


def make_desk_user(email: str) -> str:
	"""A Sales User, which is what a person using CRM's rail actually is."""
	if frappe.db.exists("User", email):
		return email

	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": "CRM Navigation",
			"user_type": "System User",
			"roles": [{"role": "Sales User"}],
		}
	).insert(ignore_permissions=True)

	return user.name
