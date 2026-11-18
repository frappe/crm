from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.booking import (
	SlotUnavailableError,
	book,
	cancel_booking,
	get_slots,
	reschedule_booking,
	to_iso,
	to_system,
)

HOSTS = ["booking-host-a@example.com", "booking-host-b@example.com"]


def next_monday() -> datetime:
	"""A Monday at least two days out, as UTC midnight."""
	today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
	day = today + timedelta(days=2)
	return day + timedelta(days=(7 - day.weekday()) % 7)


class TestBooking(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("Email Account", {"default_outgoing": 1}):
			frappe.get_doc(
				{
					"doctype": "Email Account",
					"email_account_name": "_Test Booking",
					"email_id": "booking@example.com",
					"enable_outgoing": 1,
					"default_outgoing": 1,
					"no_smtp_authentication": 1,
					"smtp_server": "localhost",
				}
			).insert(ignore_permissions=True)
		for email in HOSTS:
			if not frappe.db.exists("User", email):
				frappe.get_doc(
					{
						"doctype": "User",
						"email": email,
						"first_name": email.split("@")[0].title(),
						"roles": [{"role": "Sales User"}],
					}
				).insert(ignore_permissions=True)
		self.monday = next_monday()
		self.page = self.make_page([HOSTS[0]])

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def make_page(self, hosts, **kw):
		doc = {
			"doctype": "CRM Booking Page",
			"title": "Intro call",
			"route": frappe.generate_hash(length=8).lower(),
			"duration": 30,
			"timezone": "UTC",
			"min_notice": 0,
			"max_days_ahead": 30,
			"location_type": "Phone call",
			"hosts": [{"user": h} for h in hosts],
			"availability": [
				{"workday": d, "start_time": "09:00:00", "end_time": "12:00:00"}
				for d in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
			],
		}
		doc.update(kw)
		return frappe.get_doc(doc).insert(ignore_permissions=True)

	def at(self, hour, minute=0, days=0):
		return self.monday + timedelta(days=days, hours=hour, minutes=minute)

	def slots_on_monday(self, page=None, token=None):
		frappe.set_user("Guest")
		try:
			return get_slots((page or self.page).route, to_iso(self.monday), to_iso(self.at(24)), token)
		finally:
			frappe.set_user("Administrator")

	def book_as_guest(self, start, email="visitor@example.com", page=None, values=None):
		frappe.set_user("Guest")
		try:
			return book(
				(page or self.page).route,
				to_iso(start),
				values={"first_name": "Vera", "last_name": "Visitor", "email": email, **(values or {})},
				timezone="Europe/Paris",
			)
		finally:
			frappe.set_user("Administrator")

	def add_fields(self, page=None):
		"""Company (required) and Team size on the page's own form."""
		form = frappe.get_doc("Web Form", (page or self.page).web_form)
		form.append(
			"web_form_fields",
			{"fieldname": "organization", "fieldtype": "Data", "label": "Company", "reqd": 1},
		)
		form.append(
			"web_form_fields",
			{
				"fieldname": "no_of_employees",
				"fieldtype": "Select",
				"label": "Team size",
				"options": "1-10\n11-50\n51-200\n201-500\n501-1000\n1000+",
			},
		)
		form.save(ignore_permissions=True)

	def add_event(self, owner, start, end, **kw):
		event = frappe.get_doc(
			{
				"doctype": "Event",
				"subject": "Busy",
				"event_type": "Private",
				"starts_on": to_system(start),
				"ends_on": to_system(end),
				**kw,
			}
		).insert(ignore_permissions=True)
		event.db_set("owner", owner)
		return event

	def test_slots_follow_weekly_hours(self):
		slots = self.slots_on_monday()
		self.assertEqual(slots, [to_iso(self.at(9, m)) for m in (0, 30, 60, 90, 120, 150)])

	def test_events_and_buffer_block_slots(self):
		self.add_event(HOSTS[0], self.at(10), self.at(10, 30))
		self.assertNotIn(to_iso(self.at(10)), self.slots_on_monday())

		self.page.buffer = 15
		self.page.save()
		slots = self.slots_on_monday()
		for blocked in (self.at(9, 30), self.at(10), self.at(10, 30)):
			self.assertNotIn(to_iso(blocked), slots)
		self.assertIn(to_iso(self.at(9)), slots)

	def test_weekly_repeating_event_blocks_slots(self):
		week_before = self.at(11, days=-7)
		self.add_event(
			HOSTS[0],
			week_before,
			week_before + timedelta(minutes=30),
			repeat_this_event=1,
			repeat_on="Weekly",
			monday=1,
		)
		self.assertNotIn(to_iso(self.at(11)), self.slots_on_monday())

	def test_holidays_close_the_day(self):
		holiday_list = frappe.get_doc(
			{
				"doctype": "CRM Holiday List",
				"holiday_list_name": frappe.generate_hash(length=8),
				"from_date": self.monday.date() - timedelta(days=1),
				"to_date": self.monday.date() + timedelta(days=1),
				"holidays": [{"date": self.monday.date(), "description": "Off"}],
			}
		).insert(ignore_permissions=True)
		self.page.holiday_list = holiday_list.name
		self.page.save()
		self.assertEqual(self.slots_on_monday(), [])

	def test_booking_creates_event_and_lead_for_host(self):
		result = self.book_as_guest(self.at(9))
		booking = frappe.get_doc("CRM Booking", {"token": result["token"]})
		self.assertEqual(booking.host, HOSTS[0])
		self.assertEqual(booking.reference_doctype, "CRM Lead")

		lead = frappe.get_doc("CRM Lead", booking.reference_docname)
		self.assertEqual(lead.email, "visitor@example.com")
		self.assertEqual(lead.lead_owner, HOSTS[0])

		event = frappe.get_doc("Event", booking.event)
		self.assertEqual(event.owner, HOSTS[0])
		self.assertEqual(event.reference_docname, lead.name)
		# the guest gets the CRM's .ics; as a participant they would get its reminders too
		self.assertEqual(event.event_participants, [])
		self.assertEqual(frappe.utils.get_datetime(event.starts_on), to_system(self.at(9)))

		self.assertNotIn(to_iso(self.at(9)), self.slots_on_monday())

	def test_existing_lead_is_reused(self):
		lead = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Known", "email": "known@example.com"}
		).insert(ignore_permissions=True)
		result = self.book_as_guest(self.at(9), email="Known@Example.com")
		self.assertEqual(
			frappe.db.get_value("CRM Booking", {"token": result["token"]}, "reference_docname"), lead.name
		)

	def test_round_robin_and_taken_slot(self):
		page = self.make_page(HOSTS)
		first = self.book_as_guest(self.at(9), "one@example.com", page)
		second = self.book_as_guest(self.at(9), "two@example.com", page)
		hosts = {frappe.db.get_value("CRM Booking", {"token": r["token"]}, "host") for r in (first, second)}
		self.assertEqual(hosts, set(HOSTS))
		self.assertNotIn(to_iso(self.at(9)), self.slots_on_monday(page))
		# its own error, so the page sends the visitor back to the calendar
		with self.assertRaises(SlotUnavailableError):
			self.book_as_guest(self.at(9), "three@example.com", page)

	def test_reschedule_moves_event_and_frees_old_slot(self):
		result = self.book_as_guest(self.at(9))
		# the meeting's own time doesn't block an overlapping new time
		self.assertIn(to_iso(self.at(9)), self.slots_on_monday(token=result["token"]))

		frappe.set_user("Guest")
		reschedule_booking(result["token"], to_iso(self.at(11)))
		frappe.set_user("Administrator")

		booking = frappe.get_doc("CRM Booking", {"token": result["token"]})
		self.assertEqual(frappe.db.get_value("Event", booking.event, "starts_on"), to_system(self.at(11)))
		slots = self.slots_on_monday()
		self.assertIn(to_iso(self.at(9)), slots)
		self.assertNotIn(to_iso(self.at(11)), slots)

	def test_cancel_frees_the_slot(self):
		result = self.book_as_guest(self.at(9))
		frappe.set_user("Guest")
		cancel_booking(result["token"], "Something came up")
		frappe.set_user("Administrator")

		booking = frappe.get_doc("CRM Booking", {"token": result["token"]})
		self.assertEqual(booking.status, "Cancelled")
		self.assertEqual(frappe.db.get_value("Event", booking.event, "status"), "Cancelled")
		self.assertIn(to_iso(self.at(9)), self.slots_on_monday())
		with self.assertRaises(frappe.ValidationError):
			frappe.set_user("Guest")
			cancel_booking(result["token"])

	def test_disabled_page_is_hidden_from_guests(self):
		self.page.enabled = 0
		self.page.save()
		with self.assertRaises(frappe.DoesNotExistError):
			self.slots_on_monday()

	def test_hours_must_not_overlap(self):
		self.page.append(
			"availability", {"workday": "Monday", "start_time": "11:30:00", "end_time": "14:00:00"}
		)
		with self.assertRaises(frappe.ValidationError):
			self.page.save()

	def test_hours_must_end_after_they_start(self):
		self.page.availability[0].end_time = "08:00:00"
		with self.assertRaises(frappe.ValidationError):
			self.page.save()

	def test_each_page_gets_its_own_form_with_a_required_email(self):
		form = frappe.get_doc("Web Form", self.page.web_form)
		self.assertEqual(form.doc_type, "CRM Lead")
		self.assertEqual(next(f.reqd for f in form.web_form_fields if f.fieldname == "email"), 1)

	def test_a_deal_page_creates_a_deal(self):
		page = self.make_page([HOSTS[0]], document_type="CRM Deal")
		result = self.book_as_guest(self.at(9), email="buyer@example.com", page=page)
		booking = frappe.get_doc("CRM Booking", {"token": result["token"]})
		self.assertEqual(booking.reference_doctype, "CRM Deal")
		self.assertEqual(frappe.db.get_value("CRM Deal", booking.reference_docname, "deal_owner"), HOSTS[0])

	def test_form_answers_go_to_a_new_lead(self):
		self.add_fields()
		result = self.book_as_guest(self.at(9), values={"organization": "Acme", "no_of_employees": "11-50"})
		booking = frappe.get_doc("CRM Booking", {"token": result["token"]})
		lead = frappe.get_doc("CRM Lead", booking.reference_docname)
		self.assertEqual((lead.organization, lead.no_of_employees), ("Acme", "11-50"))
		self.assertEqual(lead.first_name, "Vera")
		self.assertEqual(frappe.parse_json(booking.answers), {"Company": "Acme", "Team size": "11-50"})

	def test_a_booking_never_changes_an_existing_lead(self):
		self.add_fields()
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Known",
				"email": "known@example.com",
				"organization": "Old Co",
			}
		).insert(ignore_permissions=True)
		before = lead.no_of_employees
		self.book_as_guest(
			self.at(9),
			email="known@example.com",
			values={"organization": "New Co", "no_of_employees": "51-200"},
		)
		lead.reload()
		# anyone can type anyone's email, so the answers stay on the booking
		self.assertEqual((lead.organization, lead.no_of_employees), ("Old Co", before))

	def test_required_form_fields_and_options_are_enforced(self):
		self.add_fields()
		with self.assertRaises(frappe.ValidationError):
			self.book_as_guest(self.at(9), values={"no_of_employees": "11-50"})
		with self.assertRaises(frappe.ValidationError):
			self.book_as_guest(self.at(9), values={"organization": "Acme", "no_of_employees": "lots"})

	def test_host_gets_a_booking_notification_not_a_guest_assignment(self):
		result = self.book_as_guest(self.at(9))
		booking = frappe.get_doc("CRM Booking", {"token": result["token"]})
		notifications = frappe.get_all(
			"CRM Notification", filters={"to_user": HOSTS[0]}, fields=["type", "message", "reference_name"]
		)
		self.assertEqual([n.type for n in notifications], ["Booking"])
		self.assertEqual(notifications[0].reference_name, booking.reference_docname)
		self.assertIn("Vera Visitor booked Intro call", notifications[0].message)

	def test_assignment_rule_leaves_a_booked_lead_with_its_host(self):
		frappe.get_doc(
			{
				"doctype": "Assignment Rule",
				"name": "Booking test round robin",
				"document_type": "CRM Lead",
				"rule": "Round Robin",
				"assign_condition": "status != 'Junk'",
				"priority": 1,
				"users": [{"user": HOSTS[1]}],
				"assignment_days": [
					{"day": d}
					for d in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
				],
			}
		).insert(ignore_permissions=True)
		# tearDown's rollback drops the rule, but not the cached list of rules for leads
		self.addCleanup(frappe.cache_manager.clear_doctype_map, "Assignment Rule", "CRM Lead")

		other = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Ruled", "email": "ruled@example.com"}
		).insert(ignore_permissions=True)
		self.assertEqual(other.get_assigned_users(), {HOSTS[1]}, "the rule should be live")

		result = self.book_as_guest(self.at(9))
		lead = frappe.get_doc(
			"CRM Lead", frappe.db.get_value("CRM Booking", {"token": result["token"]}, "reference_docname")
		)
		self.assertEqual(lead.lead_owner, HOSTS[0])
		self.assertEqual(lead.get_assigned_users(), {HOSTS[0]})

	def test_owner_keeps_an_existing_lead_and_hears_about_the_meeting(self):
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Known",
				"email": "known@example.com",
				"lead_owner": HOSTS[1],
			}
		).insert(ignore_permissions=True)
		self.book_as_guest(self.at(9), email="known@example.com")

		lead.reload()
		self.assertEqual(lead.lead_owner, HOSTS[1])
		self.assertFalse(
			frappe.db.exists(
				"DocShare", {"user": HOSTS[0], "share_doctype": "CRM Lead", "share_name": lead.name}
			),
			"booking with someone's email must not open their lead to the host",
		)
		to_owner = frappe.get_all(
			"CRM Notification", filters={"to_user": HOSTS[1], "type": "Booking"}, pluck="message"
		)
		self.assertEqual(len(to_owner), 1)
		self.assertIn("Vera Visitor booked Intro call with", to_owner[0])
		to_host = frappe.get_all(
			"CRM Notification", filters={"to_user": HOSTS[0], "type": "Booking"}, pluck="message"
		)
		self.assertEqual(len(to_host), 1)

	def test_a_sales_user_cannot_edit_or_join_someone_elses_page(self):
		frappe.set_user(HOSTS[1])
		page = frappe.get_doc("CRM Booking Page", self.page.name)
		page.append("hosts", {"user": HOSTS[1]})
		with self.assertRaises(frappe.PermissionError):
			page.save()
		self.assertFalse(frappe.has_permission("CRM Booking Page", "write", doc=self.page.name))
		self.assertTrue(frappe.has_permission("CRM Booking Page", "read", doc=self.page.name))

	def test_hosts_must_be_crm_users(self):
		website_user = "booking-website-user@example.com"
		if not frappe.db.exists("User", website_user):
			frappe.get_doc(
				{"doctype": "User", "email": website_user, "first_name": "Web", "user_type": "Website User"}
			).insert(ignore_permissions=True)
		for host in ("Guest", website_user):
			self.page.append("hosts", {"user": host})
			with self.assertRaises(frappe.ValidationError):
				self.page.save()
			self.page.reload()

	def test_a_page_cannot_take_over_another_form(self):
		other = self.make_page([HOSTS[0]])
		self.page.web_form = other.web_form
		with self.assertRaises(frappe.ValidationError):
			self.page.save()

	def test_a_sales_user_sees_only_their_bookings_and_never_the_token(self):
		result = self.book_as_guest(self.at(9))
		name = frappe.db.get_value("CRM Booking", {"token": result["token"]})
		frappe.set_user(HOSTS[1])
		self.assertEqual(frappe.get_list("CRM Booking", pluck="name"), [])
		self.assertFalse(frappe.has_permission("CRM Booking", "read", doc=name))
		frappe.set_user(HOSTS[0])
		rows = frappe.get_list("CRM Booking", fields=["name", "token"])
		self.assertEqual([r.name for r in rows], [name])
		self.assertFalse(rows[0].get("token"), "the cancel link's token is for managers only")

	def test_guest_text_is_escaped_in_the_host_email(self):
		self.add_fields()
		result = self.book_as_guest(
			self.at(9),
			values={"organization": "<form action=https://evil.example>", "no_of_employees": "1-10"},
		)
		import email

		queued = frappe.get_all(
			"Email Queue",
			filters={
				"reference_doctype": "CRM Booking",
				"reference_name": frappe.db.get_value("CRM Booking", {"token": result["token"]}),
			},
			pluck="message",
		)
		html = [
			part.get_payload(decode=True).decode()
			for message in queued
			for part in email.message_from_string(message).walk()
			if part.get_content_type() == "text/html"
		]
		self.assertTrue(any("&lt;form action=https://evil.example&gt;" in h for h in html))
		# the plain-text copy shows the answer as typed, which is harmless there
		self.assertFalse(any("<form action" in h for h in html))

	def test_one_email_cannot_fill_the_calendar(self):
		self.book_as_guest(self.at(9))
		self.book_as_guest(self.at(10))
		with self.assertRaises(frappe.ValidationError):
			self.book_as_guest(self.at(11))

	def test_meeting_links_must_be_web_links(self):
		self.page.location_type = "Custom link"
		self.page.location = "javascript:alert(1)"
		with self.assertRaises(frappe.ValidationError):
			self.page.save()

	def test_visitor_text_in_titles_and_invites_stays_harmless(self):
		from crm.api.booking import ics, plain

		self.assertEqual(plain("Claim your prize at https://evil.example now"), "Claim your prize at now")
		self.assertEqual(plain("Go to evil.example/login"), "Go to")
		result = self.book_as_guest(
			self.at(9), values={"first_name": "Eve\r\nATTENDEE:mailto:x@evil.example"}
		)
		booking = frappe.get_doc("CRM Booking", {"token": result["token"]})
		invite = ics(self.page, booking, "Host", "host@example.com", "")
		self.assertNotIn("\r\nATTENDEE:mailto:x@evil", invite)

	def test_deleting_a_page_without_bookings_removes_its_form(self):
		from crm.api.booking import list_pages

		form = self.page.web_form
		self.assertEqual(next(p for p in list_pages() if p.name == self.page.name).bookings, 0)
		frappe.delete_doc("CRM Booking Page", self.page.name)
		self.assertFalse(frappe.db.exists("Web Form", form))

	def test_a_page_with_bookings_is_kept(self):
		from crm.api.booking import list_pages

		self.book_as_guest(self.at(9))
		self.assertEqual(next(p for p in list_pages() if p.name == self.page.name).bookings, 1)
		with self.assertRaises(frappe.LinkExistsError):
			frappe.delete_doc("CRM Booking Page", self.page.name)

	# Slots taken and freed, whoever makes the change

	def booking_for(self, result):
		return frappe.get_doc("CRM Booking", {"token": result["token"]})

	def test_the_host_lock_reads_fresh_data_without_locking_events(self):
		"""Under REPEATABLE READ the reads before the lock fix a snapshot that can miss a
		booking committed while we waited. A commit after the lock starts a fresh one; a
		locking read of tabEvent instead would block every Event write and deadlock two
		bookings for different hosts."""
		from crm.api.booking import event_busy_times, lock_hosts

		with patch.dict(frappe.flags, {"in_test": False}), patch.object(frappe.db, "commit") as commit:
			lock_hosts([HOSTS[0]])
			commit.assert_called_once()
			with patch.object(frappe.db, "sql", wraps=frappe.db.sql) as sql:
				event_busy_times(HOSTS[0], self.at(9), self.at(12))
		self.assertNotIn("lock in share mode", sql.call_args.args[0].lower())
		self.assertNotIn("for update", sql.call_args.args[0].lower())

	def test_a_host_edits_only_the_questions_on_their_page_form(self):
		from crm.api.form import get_form_config, save_form

		saved = frappe.get_doc("Web Form", self.page.web_form)
		frappe.set_user(HOSTS[0])
		try:
			config = get_form_config(saved.name)
			save_form(
				saved.name,
				{
					**config,
					"published": 1,
					"route": "taken-over",
					"redirect_url": "https://evil.example",
					"document_type": "CRM Deal",
					"fields": [
						{**f, "depends_on": "eval:doc.first_name"} if f["fieldname"] == "email" else f
						for f in config["fields"]
					],
				},
			)
			without_email = [f for f in config["fields"] if f["fieldname"] != "email"]
			with self.assertRaises(frappe.ValidationError):
				save_form(saved.name, {**config, "fields": without_email})
		finally:
			frappe.set_user("Administrator")

		form = frappe.get_doc("Web Form", saved.name)
		self.assertEqual(
			(form.crm_published, form.published, form.route, form.success_url, form.doc_type),
			(saved.crm_published, saved.published, saved.route, saved.success_url, saved.doc_type),
		)
		email = next(f for f in form.web_form_fields if f.fieldname == "email")
		self.assertEqual((email.reqd, email.depends_on), (1, ""))

	def test_a_booked_slot_cannot_be_booked_again(self):
		self.book_as_guest(self.at(9), "first@example.com")
		self.assertNotIn(to_iso(self.at(9)), self.slots_on_monday())
		with self.assertRaises(SlotUnavailableError):
			self.book_as_guest(self.at(9), "second@example.com")

	def test_team_slot_frees_when_one_of_two_bookings_is_cancelled(self):
		page = self.make_page(HOSTS)
		first = self.book_as_guest(self.at(9), "one@example.com", page)
		self.book_as_guest(self.at(9), "two@example.com", page)
		self.assertNotIn(to_iso(self.at(9)), self.slots_on_monday(page))
		frappe.set_user("Guest")
		cancel_booking(first["token"])
		frappe.set_user("Administrator")
		self.assertIn(to_iso(self.at(9)), self.slots_on_monday(page))

	def test_host_cancelling_the_event_cancels_the_booking(self):
		booking = self.booking_for(self.book_as_guest(self.at(9)))
		event = frappe.get_doc("Event", booking.event)
		event.status = "Cancelled"
		event.save(ignore_permissions=True)
		booking.reload()
		self.assertEqual(booking.status, "Cancelled")
		self.assertIn(to_iso(self.at(9)), self.slots_on_monday())
		self.assertTrue(
			frappe.db.exists(
				"Email Queue Recipient", {"recipient": booking.guest_email, "parenttype": "Email Queue"}
			)
		)

	def test_host_deleting_the_event_cancels_the_booking(self):
		booking = self.booking_for(self.book_as_guest(self.at(9)))
		frappe.delete_doc("Event", booking.event, ignore_permissions=True)
		booking.reload()
		self.assertEqual((booking.status, booking.event), ("Cancelled", None))
		self.assertIn(to_iso(self.at(9)), self.slots_on_monday())

	def test_host_moving_the_event_moves_the_booking(self):
		booking = self.booking_for(self.book_as_guest(self.at(9)))
		event = frappe.get_doc("Event", booking.event)
		event.starts_on, event.ends_on = to_system(self.at(11)), to_system(self.at(11, 30))
		event.save(ignore_permissions=True)
		booking.reload()
		self.assertEqual(frappe.utils.get_datetime(booking.starts_on), to_system(self.at(11)))
		slots = self.slots_on_monday()
		self.assertIn(to_iso(self.at(9)), slots)
		self.assertNotIn(to_iso(self.at(11)), slots)

	def test_cancelling_and_rebooking_the_same_slot(self):
		first = self.book_as_guest(self.at(9))
		frappe.set_user("Guest")
		cancel_booking(first["token"])
		frappe.set_user("Administrator")
		second = self.book_as_guest(self.at(9), "again@example.com")
		self.assertEqual(self.booking_for(second).status, "Confirmed")
		self.assertNotIn(to_iso(self.at(9)), self.slots_on_monday())

	def test_filters_tell_nothing_about_hidden_events(self):
		"""The caller's filters must not use a hidden event to fill the page: what came
		back would tell whether that event matched, a letter at a time."""
		from crm.api.event import get_event_list

		hidden = self.add_event(HOSTS[0], self.at(11), self.at(11, 30), subject="Secret plan")
		mine = self.add_event(HOSTS[1], self.at(13), self.at(13, 30))
		frappe.set_user(HOSTS[1])
		try:

			def probe(prefix):
				return get_event_list(
					"Event",
					["name"],
					{"name": ["in", [mine.name, hidden.name]]},
					[["name", "=", mine.name], ["subject", "like", f"{prefix}%"]],
					"creation asc",
					1,
				)

			self.assertEqual([r.name for r in probe("Secret")], [mine.name])
			self.assertEqual([r.name for r in probe("Nothing")], [mine.name])
			participants = get_event_list(
				"Event Participants", ["name", "parent"], {"parent": ["in", [hidden.name]]}
			)
			self.assertEqual(participants, [])
		finally:
			frappe.set_user("Administrator")

	def test_teammates_see_a_booked_meeting_on_the_lead_but_not_private_ones(self):
		from crm.api.event import get_event, get_event_list

		manager = "booking-manager@example.com"
		if not frappe.db.exists("User", manager):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": manager,
					"first_name": "Manager",
					"roles": [{"role": "Sales Manager"}],
				}
			).insert(ignore_permissions=True)
		booking = self.booking_for(self.book_as_guest(self.at(9)))
		private = self.add_event(HOSTS[0], self.at(11), self.at(11, 30))
		on_lead = {"reference_doctype": "CRM Lead", "reference_docname": booking.reference_docname}
		try:
			# a manager can read the lead, so sees its meeting, but not the host's own
			frappe.set_user(manager)
			self.assertEqual([e.name for e in get_event_list("Event", ["name"], on_lead)], [booking.event])
			self.assertEqual(get_event(booking.event)["name"], booking.event)
			self.assertNotIn(
				private.name, [e.name for e in get_event_list("Event", ["name"], {"owner": HOSTS[0]})]
			)
			with self.assertRaises(frappe.PermissionError):
				get_event(private.name)
			# a sales user outside the host's team can't read the lead, so sees neither
			frappe.set_user(HOSTS[1])
			self.assertEqual(get_event_list("Event", ["name"], on_lead), [])
		finally:
			frappe.set_user("Administrator")

	def test_meeting_title_can_be_configured(self):
		booking = self.booking_for(self.book_as_guest(self.at(9)))
		self.assertEqual(frappe.db.get_value("Event", booking.event, "subject"), "Intro call (Vera Visitor)")

		self.page.event_title = "Demo · {guest} · {page} · {unknown}"
		self.page.save()
		booking = self.booking_for(self.book_as_guest(self.at(10), "second@example.com"))
		self.assertEqual(
			frappe.db.get_value("Event", booking.event, "subject"),
			"Demo · Vera Visitor · Intro call · {unknown}",
		)

	def test_booked_meetings_carry_the_guest_so_the_crm_can_warn_before_emailing(self):
		from crm.api.event import get_event, get_event_list

		booking = self.booking_for(self.book_as_guest(self.at(9)))
		other = self.add_event(HOSTS[0], self.at(11), self.at(11, 30))
		frappe.set_user(HOSTS[0])
		try:
			guests = {e.name: e.booking_guest for e in get_event_list("Event", ["name"], {"owner": HOSTS[0]})}
			self.assertEqual(guests, {booking.event: "visitor@example.com", other.name: None})
			self.assertEqual(get_event(booking.event)["booking_guest"], "visitor@example.com")
		finally:
			frappe.set_user("Administrator")

		cancel_booking(booking.token)
		frappe.set_user(HOSTS[0])
		try:
			self.assertIsNone(get_event(booking.event)["booking_guest"])
		finally:
			frappe.set_user("Administrator")

	def connect_google(self, user):
		# skips Google Settings validation; nothing here talks to Google
		frappe.get_doc(
			{
				"doctype": "Google Calendar",
				"calendar_name": user,
				"user": user,
				"enable": 1,
				"pull_from_google_calendar": 1,
				"push_to_google_calendar": 1,
			}
		).db_insert()
		from frappe.utils.password import set_encrypted_password

		set_encrypted_password("Google Calendar", user, "refresh-token", "refresh_token")

	def test_guests_get_a_reminder_ahead_of_the_meeting(self):
		from crm.api.booking import send_guest_reminders

		self.page.guest_reminder = "1 day before"
		self.page.save()
		booking = self.booking_for(self.book_as_guest(self.at(9)))
		self.assertEqual(booking.reminder_sent, 0)

		# not yet: the meeting is more than a day away
		send_guest_reminders()
		self.assertEqual(frappe.db.get_value("CRM Booking", booking.name, "reminder_sent"), 0)

		# a day out, it goes once, to the guest only
		booking.db_set("starts_on", to_system(datetime.now(UTC) + timedelta(hours=20)))
		with patch("crm.api.booking.frappe.sendmail") as sendmail:
			send_guest_reminders()
			send_guest_reminders()
		self.assertEqual(frappe.db.get_value("CRM Booking", booking.name, "reminder_sent"), 1)
		self.assertEqual(len(sendmail.call_args_list), 1)
		sent = sendmail.call_args.kwargs
		self.assertEqual(sent["recipients"], ["visitor@example.com"])
		self.assertTrue(sent["subject"].startswith("Reminder: Intro call"))
		self.assertEqual(sent["args"]["action"], "reminder")

	def test_moving_a_meeting_sets_up_a_new_reminder(self):
		self.page.guest_reminder = "1 hour before"
		self.page.save()
		booking = self.booking_for(self.book_as_guest(self.at(9)))
		booking.db_set("reminder_sent", 1)
		reschedule_booking(booking.token, to_iso(self.at(10)))
		self.assertEqual(frappe.db.get_value("CRM Booking", booking.name, "reminder_sent"), 0)

	def test_no_reminder_when_booked_inside_the_window_or_turned_off(self):
		self.page.guest_reminder = "1 day before"
		self.page.save()
		soon = self.make_page([HOSTS[1]], guest_reminder="1 day before", min_notice=0)
		booking = frappe.get_doc(
			{
				"doctype": "CRM Booking",
				"booking_page": soon.name,
				"host": HOSTS[1],
				"starts_on": to_system(datetime.now(UTC) + timedelta(hours=3)),
				"ends_on": to_system(datetime.now(UTC) + timedelta(hours=3, minutes=30)),
				"guest_name": "Soon",
				"guest_email": "soon@example.com",
				"token": frappe.generate_hash(),
			}
		).insert(ignore_permissions=True)
		self.assertEqual(booking.reminder_sent, 1)

		off = self.make_page([HOSTS[1]], guest_reminder="No reminder")
		booking = self.booking_for(self.book_as_guest(self.at(11), "off@example.com", off))
		self.assertEqual(booking.reminder_sent, 1)

	def test_google_busy_times_block_slots(self):
		self.connect_google(HOSTS[0])
		busy = [(to_iso(self.at(10)), to_iso(self.at(11)))]
		with patch("crm.api.booking.fetch_google_busy", return_value=busy):
			frappe.cache.delete_keys("crm_booking_google_busy")
			slots = self.slots_on_monday()
		self.assertIn(to_iso(self.at(9, 30)), slots)
		self.assertNotIn(to_iso(self.at(10)), slots)
		self.assertNotIn(to_iso(self.at(10, 30)), slots)
		self.assertIn(to_iso(self.at(11)), slots)

	def test_a_booking_survives_google_being_unreachable(self):
		from crm.api.booking import hosts_without_google

		self.page.location_type = "Google Meet"
		self.page.save()
		self.assertEqual(hosts_without_google([HOSTS[0]]), [HOSTS[0]])
		self.connect_google(HOSTS[0])
		self.assertEqual(hosts_without_google([HOSTS[0]]), [])

		def google_down(doc, method=None):
			if doc.sync_with_google_calendar:
				raise ConnectionError("Google is down")

		with (
			patch("crm.api.booking.fetch_google_busy", return_value=[]),
			patch(
				"frappe.integrations.doctype.google_calendar.google_calendar.insert_event_in_google_calendar",
				google_down,
			),
			patch("crm.api.booking.frappe.sendmail") as sendmail,
		):
			booking = self.booking_for(self.book_as_guest(self.at(9)))
		event = frappe.get_doc("Event", booking.event)
		self.assertEqual(event.owner, HOSTS[0])
		self.assertFalse(event.sync_with_google_calendar)
		# no Meet link, so the host is told to send one
		host_mail = next(c.kwargs for c in sendmail.call_args_list if c.kwargs["recipients"] == [HOSTS[0]])
		self.assertIn("Send Vera Visitor a link to join", host_mail["args"]["note"])

	def test_google_status_for_page_settings(self):
		from crm.api.booking import google_status

		frappe.db.set_single_value("Google Settings", "enable", 0)
		self.assertEqual(google_status([HOSTS[0]])["configured"], False)
		frappe.db.set_single_value("Google Settings", "enable", 1)
		self.assertEqual(google_status(HOSTS)["unconnected"], HOSTS)
		# a calendar that was never authorized doesn't count
		frappe.get_doc(
			{
				"doctype": "Google Calendar",
				"calendar_name": "half",
				"user": HOSTS[1],
				"enable": 1,
				"push_to_google_calendar": 1,
			}
		).db_insert()
		self.connect_google(HOSTS[0])
		self.assertEqual(google_status(HOSTS)["unconnected"], [HOSTS[1]])
		# Google's own callback stores the token on the record, not encrypted
		frappe.db.set_value("Google Calendar", "half", "refresh_token", "from-google")
		self.assertEqual(google_status(HOSTS)["unconnected"], [])
		frappe.set_user(HOSTS[0])
		self.assertEqual(google_status([HOSTS[0]])["my_calendar"], HOSTS[0])

	def test_a_host_another_booking_is_holding_cant_be_booked(self):
		from crm.api import booking as api

		other = frappe.cache.lock(frappe.cache.make_key(f"crm_booking_host:{HOSTS[0]}"), timeout=10)
		other.acquire()
		try:
			with patch.object(api, "HOST_LOCK_SECONDS", 1), self.assertRaises(SlotUnavailableError):
				self.book_as_guest(self.at(9))
		finally:
			other.release()
		# the same transaction can book the host again without waiting on itself
		self.book_as_guest(self.at(9))
		self.book_as_guest(self.at(10), "second@example.com")

	def test_conditional_fields_hold_without_the_page(self):
		form = frappe.get_doc("Web Form", self.page.web_form)
		form.append("web_form_fields", {"fieldname": "organization", "fieldtype": "Data", "label": "Company"})
		form.append(
			"web_form_fields",
			{
				"fieldname": "website",
				"fieldtype": "Data",
				"label": "Website",
				"mandatory_depends_on": 'eval:doc.organization == "Acme"',
			},
		)
		form.append(
			"web_form_fields",
			{"fieldname": "job_title", "fieldtype": "Data", "label": "Role", "depends_on": "organization"},
		)
		form.save(ignore_permissions=True)

		# "required if" holds for an API call that never ran the page's script
		with self.assertRaises(frappe.ValidationError):
			self.book_as_guest(self.at(9), values={"organization": "Acme"})
		# an answer to a field the form hides is ignored
		booking = self.booking_for(self.book_as_guest(self.at(9), values={"job_title": "CEO"}))
		self.assertNotIn("Role", frappe.parse_json(booking.answers))
		self.assertFalse(frappe.db.get_value("CRM Lead", booking.reference_docname, "job_title"))

	def test_limits_cannot_be_negative(self):
		# a negative step would never reach the end of the day
		self.page.slot_interval = -15
		with self.assertRaises(frappe.ValidationError):
			self.page.save()

	def test_a_turned_off_page_previews_but_takes_no_bookings(self):
		self.page.enabled = 0
		self.page.save()
		self.assertIn(
			to_iso(self.at(9)), get_slots(self.page.route, to_iso(self.monday), to_iso(self.at(24)))
		)
		with self.assertRaises(frappe.DoesNotExistError):
			book(self.page.route, to_iso(self.at(9)), values={"first_name": "Vera", "email": "v@example.com"})

	def test_guest_email_is_one_bare_address(self):
		booking = self.booking_for(self.book_as_guest(self.at(9), " Vera@Example.com "))
		self.assertEqual(booking.guest_email, "vera@example.com")
		with self.assertRaises(frappe.ValidationError):
			self.book_as_guest(self.at(10), "a@example.com, b@example.com")

	def test_meeting_of_a_guest_cancelled_booking_can_be_deleted(self):
		result = self.book_as_guest(self.at(9))
		frappe.set_user("Guest")
		cancel_booking(result["token"])
		frappe.set_user("Administrator")
		booking = self.booking_for(result)
		frappe.delete_doc("Event", booking.event, ignore_permissions=True)
		booking.reload()
		self.assertEqual((booking.status, booking.event), ("Cancelled", None))

	def test_guest_can_cancel_and_move_when_google_rejects_the_change(self):
		def google_down(doc, method=None):
			raise ConnectionError("Google is down")

		result = self.book_as_guest(self.at(9))
		event = self.booking_for(result).event
		hook = "frappe.integrations.doctype.google_calendar.google_calendar.update_event_in_google_calendar"
		frappe.set_user("Guest")
		try:
			with patch(hook, google_down):
				frappe.db.set_value("Event", event, "sync_with_google_calendar", 1)
				reschedule_booking(result["token"], to_iso(self.at(10)))
				cancel_booking(result["token"])
		finally:
			frappe.set_user("Administrator")
		self.assertEqual(
			frappe.db.get_value("Event", event, ["status", "starts_on"]),
			("Cancelled", to_system(self.at(10))),
		)

	def test_google_not_answering_is_not_remembered_as_free(self):
		self.connect_google(HOSTS[0])
		frappe.cache.delete_keys("crm_booking_google_busy")
		with patch("crm.api.booking.fetch_google_busy", return_value=None):
			self.assertIn(to_iso(self.at(10)), self.slots_on_monday())
		busy = [(to_iso(self.at(10)), to_iso(self.at(11)))]
		with patch("crm.api.booking.fetch_google_busy", return_value=busy):
			self.assertNotIn(to_iso(self.at(10)), self.slots_on_monday())

	def test_google_status_needs_a_page_editor_and_checks_only_crm_users(self):
		from crm.api.booking import google_status, hosts_without_google

		self.assertEqual(hosts_without_google(["Guest", HOSTS[0]]), [HOSTS[0]])
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			google_status(HOSTS)

	def test_a_manager_inside_the_sales_hierarchy_sees_only_their_teams_bookings(self):
		from crm.fcrm.doctype.crm_booking.crm_booking import sees_all_bookings

		manager = "booking-manager@example.com"
		if not frappe.db.exists("User", manager):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": manager,
					"first_name": "Mona",
					"roles": [{"role": "Sales Manager"}],
				}
			).insert(ignore_permissions=True)
		self.assertTrue(sees_all_bookings(manager))
		frappe.get_doc({"doctype": "CRM Sales Hierarchy", "user": manager}).insert(ignore_permissions=True)
		frappe.db.set_single_value("FCRM Settings", "enable_sales_hierarchy", 1)
		self.assertFalse(sees_all_bookings(manager))

	def test_event_lists_take_only_plain_fields(self):
		from crm.api.event import get_event_list

		self.add_event(HOSTS[0], self.at(9), self.at(10))
		frappe.set_user(HOSTS[1])
		self.assertTrue(get_event_list("Event", fields=["name", "subject"]) is not None)
		with self.assertRaises(frappe.PermissionError):
			get_event_list("Event", fields=["name", "subject", "google_calendar as name"])
		linked = [["google_calendar.calendar_name", "like", "a%"]]
		for filters, or_filters in (
			(linked, None),
			(None, linked),
			({"google_calendar.user": HOSTS[0]}, None),
		):
			with self.assertRaises(frappe.PermissionError):
				get_event_list("Event", ["name"], filters, or_filters)
		for shape in (
			[["Google Calendar", "calendar_name", "like", "a%"]],
			[["google_calendar.calendar_name", "a%"]],
			[["Event", "google_calendar.calendar_name", "like", "a%", None]],
		):
			with self.assertRaises(frappe.PermissionError):
				get_event_list("Event", ["name"], shape)
		get_event_list("Event", ["name"], [["Event Participants", "email", "like", "a%"]])
		get_event_list("Event", ["name"], order_by="starts_on asc, creation DESC")
		for order_by in ("google_calendar.calendar_name asc", "`tabGoogle Calendar`.calendar_name"):
			with self.assertRaises(frappe.PermissionError):
				get_event_list("Event", ["name"], order_by=order_by)

	def test_an_events_owner_can_delete_it(self):
		from crm.api.event import delete_event

		own = self.add_event(HOSTS[0], self.at(9), self.at(10))
		other = self.add_event(HOSTS[1], self.at(11), self.at(12))
		frappe.set_user(HOSTS[0])
		delete_event(own.name)
		with self.assertRaises(frappe.PermissionError):
			delete_event(other.name)
		frappe.set_user("Administrator")
		self.assertFalse(frappe.db.exists("Event", own.name))
		self.assertTrue(frappe.db.exists("Event", other.name))

	def test_a_synced_meeting_never_has_google_mail_the_guest(self):
		"""Google mails a meeting's description, which holds the guest's own answers, to
		every participant from the host's account; the guest gets the CRM's .ics instead."""
		self.connect_google(HOSTS[0])
		with (
			patch("crm.api.booking.fetch_google_busy", return_value=[]),
			patch(
				"frappe.integrations.doctype.google_calendar.google_calendar.insert_event_in_google_calendar"
			),
		):
			booking = self.booking_for(self.book_as_guest(self.at(9), "someone-else@example.com"))
		event = frappe.get_doc("Event", booking.event)
		self.assertTrue(event.sync_with_google_calendar)
		self.assertEqual(event.event_participants, [])
		self.assertEqual(event.reference_docname, booking.reference_docname)
		messages = frappe.get_all(
			"Email Queue",
			filters={"reference_doctype": "CRM Booking", "reference_name": booking.name},
			pluck="message",
		)
		self.assertTrue(any("invite.ics" in m for m in messages))

	def test_a_meeting_cancelled_in_google_cancels_its_booking(self):
		from crm.api.booking import cancel_bookings_closed_elsewhere

		booking = self.booking_for(self.book_as_guest(self.at(9)))
		# Google's pull closes the Event straight in the database, so no hook runs
		frappe.db.set_value("Event", booking.event, "status", "Closed")
		cancel_bookings_closed_elsewhere()
		booking.reload()
		self.assertEqual(booking.status, "Cancelled")

	def test_closing_a_past_meeting_keeps_its_booking(self):
		booking = self.booking_for(self.book_as_guest(self.at(9)))
		past = frappe.utils.add_days(frappe.utils.now_datetime(), -1)
		booking.db_set({"starts_on": past, "ends_on": frappe.utils.add_to_date(past, minutes=30)})
		event = frappe.get_doc("Event", booking.event)
		event.status = "Closed"
		event.save(ignore_permissions=True)
		booking.reload()
		self.assertEqual(booking.status, "Confirmed")

		frappe.delete_doc("Event", booking.event, ignore_permissions=True)
		booking.reload()
		self.assertEqual((booking.status, booking.event), ("Confirmed", None))

	def test_a_meeting_marked_completed_keeps_its_booking(self):
		from crm.api.booking import cancel_bookings_closed_elsewhere

		booking = self.booking_for(self.book_as_guest(self.at(9)))
		frappe.db.set_value("Event", booking.event, "status", "Completed")
		cancel_bookings_closed_elsewhere()
		booking.reload()
		self.assertEqual(booking.status, "Confirmed")

	def guest_invites(self, booking):
		import email

		return [
			part.get_payload(decode=True).decode()
			for message in frappe.get_all(
				"Email Queue",
				filters={"reference_doctype": "CRM Booking", "reference_name": booking.name},
				pluck="message",
				order_by="creation asc",
			)
			for part in email.message_from_string(message).walk()
			if part.get_filename() == "invite.ics"
		]

	def test_guest_invites_update_and_cancel_the_same_calendar_entry(self):
		import re

		def later(seconds):
			return patch(
				"frappe.model.document.now", return_value=str(frappe.utils.add_to_date(None, seconds=seconds))
			)

		booking = self.booking_for(self.book_as_guest(self.at(9)))
		with later(5):
			frappe.set_user("Guest")
			reschedule_booking(booking.token, to_iso(self.at(10)))
			frappe.set_user("Administrator")
		with later(10):
			cancel_booking(booking.token)
		invites = self.guest_invites(booking)
		self.assertEqual(len(invites), 3)
		uids = {re.search(r"UID:(\S+)", i).group(1) for i in invites}
		sequences = [int(re.search(r"SEQUENCE:(\d+)", i).group(1)) for i in invites]
		self.assertEqual(len(uids), 1)
		self.assertEqual(sequences, sorted(set(sequences)))
		self.assertIn("METHOD:CANCEL", invites[-1])
		self.assertIn("STATUS:CANCELLED", invites[-1])

	def test_a_number_answered_zero_is_kept(self):
		form = frappe.get_doc("Web Form", self.page.web_form)
		form.append(
			"web_form_fields",
			{"fieldname": "annual_revenue", "fieldtype": "Currency", "label": "Revenue", "reqd": 1},
		)
		form.save(ignore_permissions=True)
		booking = self.booking_for(self.book_as_guest(self.at(9), values={"annual_revenue": 0}))
		self.assertEqual(booking.status, "Confirmed")

	def test_round_robin_skips_cancelled_bookings(self):
		from crm.api.booking import pick_host

		page = self.make_page(HOSTS)
		first = self.booking_for(self.book_as_guest(self.at(9), "one@example.com", page))
		second = self.booking_for(self.book_as_guest(self.at(10), "two@example.com", page))
		# the later host's guest cancels, so that host is the one booked longest ago
		later = max((first, second), key=lambda b: b.creation)
		cancel_booking(later.token)
		self.assertEqual(pick_host(page, list(HOSTS)), later.host)

	def test_a_merged_google_block_frees_only_the_bookings_own_time(self):
		from crm.api.booking import without

		own = (self.at(9), self.at(9, 30))
		self.assertEqual(without([(self.at(9), self.at(10))], own), [(self.at(9, 30), self.at(10))])
		self.assertEqual(without([(self.at(8), self.at(8, 30))], own), [(self.at(8), self.at(8, 30))])
		self.assertEqual(without([(self.at(9), self.at(9, 30))], own), [])

	def test_cancelling_clears_the_cached_google_day(self):
		from crm.api.booking import google_busy_key

		self.connect_google(HOSTS[0])
		with patch("crm.api.booking.fetch_google_busy", return_value=[]):
			booking = self.booking_for(self.book_as_guest(self.at(9)))
		day = self.at(9).replace(hour=0, minute=0)
		key = google_busy_key(HOSTS[0], day)
		frappe.cache.set_value(key, [(to_iso(self.at(9)), to_iso(self.at(9, 30)))])
		cancel_booking(booking.token)
		self.assertIsNone(frappe.cache.get_value(key))

	def test_a_manager_cannot_hide_the_booking_email_either(self):
		from crm.api.form import get_form_config, save_form

		config = get_form_config(self.page.web_form)
		fields = [
			{**f, "depends_on": "eval:doc.first_name", "reqd": 0} if f["fieldname"] == "email" else f
			for f in config["fields"]
		]
		save_form(self.page.web_form, {**config, "fields": fields})
		form = frappe.get_doc("Web Form", self.page.web_form)
		email = next(f for f in form.web_form_fields if f.fieldname == "email")
		self.assertEqual((email.reqd, email.depends_on), (1, ""))
