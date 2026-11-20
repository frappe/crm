# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import re
from itertools import pairwise
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_time


class CRMBookingPage(Document):
	def validate(self):
		self.route = re.sub(r"[^a-z0-9-]+", "-", (self.route or self.title).strip().lower()).strip("-")
		if not self.route:
			frappe.throw(_("Route is required"))
		if self.duration <= 0:
			frappe.throw(_("Duration must be more than zero"))
		for field in ("slot_interval", "buffer", "min_notice", "max_days_ahead"):
			if (self.get(field) or 0) < 0:
				frappe.throw(_("{0} can't be negative").format(_(self.meta.get_label(field))))
		if self.timezone:
			try:
				ZoneInfo(self.timezone)
			except (ZoneInfoNotFoundError, ValueError):
				frappe.throw(_("{0} is not a valid timezone").format(self.timezone))
		self.validate_hours()
		self.validate_editor()
		self.validate_hosts()
		self.validate_location()
		self.ensure_form()

	def validate_editor(self):
		"""Sales Users edit only pages they host. Checked against the saved hosts, so
		nobody can add themselves to someone else's page."""
		if is_page_manager() or self.is_new():
			return
		saved = frappe.get_all(
			"CRM Booking Page Host", filters={"parent": self.name, "parenttype": self.doctype}, pluck="user"
		)
		if frappe.session.user not in saved:
			frappe.throw(_("Only this page's hosts can change it"), frappe.PermissionError)

	def validate_hosts(self):
		hosts = [h.user for h in self.hosts]
		if len(hosts) != len(set(hosts)):
			frappe.throw(_("A host is listed more than once"))
		allowed = crm_users(hosts)
		for host in hosts:
			if host not in allowed:
				frappe.throw(_("{0} can't host bookings: they aren't a CRM user").format(host))

	def validate_location(self):
		if self.location_type == "Custom link" and self.location:
			if not re.match(r"^https?://", self.location.strip(), re.IGNORECASE):
				frappe.throw(_("The meeting link must start with https:// or http://"))

	def validate_hours(self):
		by_day = {}
		for row in self.availability:
			start, end = get_time(row.start_time), get_time(row.end_time)
			if start >= end:
				frappe.throw(_("{0}: end time must be after the start time").format(_(row.workday)))
			by_day.setdefault(row.workday, []).append((start, end))
		for day, ranges in by_day.items():
			ranges.sort()
			for (_start, prev_end), (next_start, _end) in pairwise(ranges):
				if next_start < prev_end:
					frappe.throw(_("{0}: hours overlap").format(_(day)))

	def ensure_form(self):
		"""Each page owns a CRM web form for its document type, created with the page.
		Bookings need an email, so the form always asks for one."""
		from crm.api.form import _save_form

		if not self.is_new() and self.has_value_changed("web_form"):
			frappe.throw(_("A booking page's form can't be swapped for another"))
		if self.web_form and not is_own_form(self.web_form, self.name):
			frappe.throw(_("A booking page can only use the form made for it"))
		if not self.web_form:
			# Web Forms are named after their title, so make it unique; it's never shown
			key = frappe.generate_hash(length=10).lower()
			self.web_form = _save_form(
				None,
				{
					"title": f"{self.title} (booking {key})",
					"route": f"crm-booking-{key}",
					"document_type": self.document_type or "CRM Lead",
					"published": 0,
				},
			)["name"]
		form = frappe.get_doc("Web Form", self.web_form)
		if form.doc_type != self.document_type:
			frappe.throw(_("This page's form creates a {0}").format(_(form.doc_type)))
		email = next((f for f in form.web_form_fields if f.fieldname == "email"), None)
		if not email:
			frappe.throw(_("The form needs an Email field, so people can be sent their booking"))
		if not email.reqd:
			email.db_set("reqd", 1)

	def after_delete(self):
		# the page's own form goes with it (bookings block deleting a page that has any)
		if self.web_form and frappe.db.exists("Web Form", self.web_form) and is_own_form(self.web_form):
			frappe.delete_doc("Web Form", self.web_form, ignore_permissions=True, force=True)


def is_page_manager(user: str | None = None) -> bool:
	return bool({"System Manager", "Sales Manager"} & set(frappe.get_roles(user)))


def is_own_form(web_form: str, page: str | None = None) -> bool:
	"""Whether `web_form` is one a booking page made for itself, and no other page uses it."""
	if not (frappe.db.get_value("Web Form", web_form, "route") or "").startswith("crm-booking-"):
		return False
	others = frappe.get_all(
		"CRM Booking Page", filters={"web_form": web_form, "name": ["!=", page or ""]}, limit=1
	)
	return not others


def has_permission(doc, ptype, user=None):
	"""Anyone in sales can see pages; a Sales User changes or deletes only pages they host."""
	if ptype in ("read", "select", "print", "email", "report", "export", "share") or is_page_manager(user):
		return True
	if doc.is_new():
		return True
	user = user or frappe.session.user
	return bool(
		frappe.db.exists(
			"CRM Booking Page Host", {"parent": doc.name, "parenttype": doc.doctype, "user": user}
		)
	)


def crm_users(users: list[str]) -> set[str]:
	"""The users who can host bookings: System Users with a CRM role."""
	with_role = frappe.get_all(
		"Has Role",
		filters={
			"parenttype": "User",
			"parent": ["in", users or [""]],
			"role": ["in", ["Sales User", "Sales Manager", "System Manager"]],
		},
		pluck="parent",
	)
	system_users = frappe.get_all(
		"User", filters={"name": ["in", users or [""]], "user_type": "System User"}, pluck="name"
	)
	return (set(with_role) & set(system_users)) - {"Guest"}
