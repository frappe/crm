from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.extends.notification_log import before_insert, get_crm_route


class TestNotificationLogLink(IntegrationTestCase):
	def test_get_crm_route_lead(self):
		self.assertEqual(get_crm_route("CRM Lead", "CRM-LEAD-0001"), "/crm/leads/CRM-LEAD-0001")

	def test_get_crm_route_deal(self):
		self.assertEqual(get_crm_route("CRM Deal", "CRM-DEAL-0001"), "/crm/deals/CRM-DEAL-0001")

	def test_get_crm_route_non_crm_doctype(self):
		"""Non-CRM documents get no CRM route (email keeps the Desk fallback)."""
		self.assertIsNone(get_crm_route("ToDo", "abc123"))

	def test_get_crm_route_missing_name(self):
		self.assertIsNone(get_crm_route("CRM Lead", None))

	def test_get_crm_route_task_links_to_parent(self):
		"""Tasks have no standalone page; link to the parent Lead/Deal Tasks tab."""
		parent = frappe._dict(reference_doctype="CRM Deal", reference_docname="CRM-DEAL-0009")
		with patch("frappe.db.get_value", return_value=parent):
			self.assertEqual(get_crm_route("CRM Task", "task-1"), "/crm/deals/CRM-DEAL-0009#tasks")

	def test_get_crm_route_task_without_parent(self):
		with patch("frappe.db.get_value", return_value=None):
			self.assertIsNone(get_crm_route("CRM Task", "task-orphan"))

	def test_before_insert_sets_crm_link(self):
		doc = frappe._dict(link=None, document_type="CRM Lead", document_name="CRM-LEAD-0002")
		before_insert(doc)
		self.assertEqual(doc.link, frappe.utils.get_url("/crm/leads/CRM-LEAD-0002"))

	def test_before_insert_preserves_existing_link(self):
		doc = frappe._dict(link="/custom/link", document_type="CRM Lead", document_name="CRM-LEAD-0003")
		before_insert(doc)
		self.assertEqual(doc.link, "/custom/link")

	def test_before_insert_ignores_non_crm_doc(self):
		doc = frappe._dict(link=None, document_type="ToDo", document_name="abc")
		before_insert(doc)
		self.assertIsNone(doc.link)

	def test_before_insert_is_type_agnostic(self):
		"""Covers assign AND unassign: both emit type='Assignment' logs, but the link is
		set purely from the CRM document_type, so any notification type is handled."""
		for notification_type in ("Assignment", "Share", "Default", None):
			doc = frappe._dict(
				link=None,
				type=notification_type,
				document_type="CRM Deal",
				document_name="CRM-DEAL-0004",
			)
			before_insert(doc)
			self.assertEqual(doc.link, frappe.utils.get_url("/crm/deals/CRM-DEAL-0004"))
