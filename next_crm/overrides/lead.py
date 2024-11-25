# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import json

import frappe
from frappe import _
from frappe.desk.form.assign_to import add as assign

from frappe.utils import has_gravatar, validate_email_address
from erpnext.crm.doctype.lead.lead import Lead
from next_crm.ncrm.doctype.crm_service_level_agreement.utils import get_sla
from next_crm.ncrm.doctype.crm_status_change_log.crm_status_change_log import add_status_change_log


class Lead(Lead):

	def before_validate(self):
		self.set_sla()
		super()

	def validate(self):
		super()
		if not self.is_new() and self.has_value_changed("lead_owner") and self.lead_owner:
			self.share_with_agent(self.lead_owner)
			self.assign_agent(self.lead_owner)
		if self.has_value_changed("status"):
			add_status_change_log(self)

	def after_insert(self):
		if self.lead_owner:
			self.assign_agent(self.lead_owner)
		super()

	def before_save(self):
		self.apply_sla()
		super()

	def validate_email(self):
		if self.email:
			if not self.flags.ignore_email_validation:
				validate_email_address(self.email, throw=True)

			if self.email == self.lead_owner:
				frappe.throw(_("Lead Owner cannot be same as the Lead Email Address"))

			if self.is_new() or not self.image:
				self.image = has_gravatar(self.email)

	def assign_agent(self, agent):
		if not agent:
			return

		assignees = self.get_assigned_users()
		if assignees:
			for assignee in assignees:
				if agent == assignee:
					# the agent is already set as an assignee
					return

		assign({"assign_to": [agent], "doctype": "Lead", "name": self.name})

	def share_with_agent(self, agent):
		if not agent:
			return

		docshares = frappe.get_all(
			"DocShare",
			filters={"share_name": self.name, "share_doctype": self.doctype},
			fields=["name", "user"],
		)

		shared_with = [d.user for d in docshares] + [agent]

		for user in shared_with:
			if user == agent and not frappe.db.exists("DocShare", {"user": agent, "share_name": self.name, "share_doctype": self.doctype}):
				frappe.share.add_docshare(
					self.doctype, self.name, agent, write=1, flags={"ignore_share_permission": True}
				)
			elif user != agent:
				frappe.share.remove(self.doctype, self.name, user)

	def create_contact(self, throw=False):
		if not self.lead_name:
			self.set_full_name()
			self.set_lead_name()

		existing_contact = self.contact_exists(throw)
		if existing_contact:
			return existing_contact

		contact = frappe.new_doc("Contact")
		contact.update(
			{
				"first_name": self.first_name or self.lead_name,
				"last_name": self.last_name,
				"salutation": self.salutation,
				"gender": self.gender,
				"designation": self.job_title,
				"company_name": self.customer,
				"image": self.image or "",
			}
		)

		if self.email_id:
			contact.append("email_ids", {"email_id": self.email_id, "is_primary": 1})

		if self.phone:
			contact.append("phone_nos", {"phone": self.phone, "is_primary_phone": 1})

		if self.mobile_no:
			contact.append("phone_nos", {"phone": self.mobile_no, "is_primary_mobile_no": 1})

		contact.insert(ignore_permissions=True)
		contact.reload()  # load changes by hooks on contact

		return contact.name

	def create_customer(self):
		if not self.company_name:
			return

		existing_customer = frappe.db.exists("Customer", {"customer_name": self.company_name})
		if existing_customer:
			return existing_customer

		customer = frappe.new_doc("Customer")
		customer.update(
			{
				"customer_name": self.company_name,
				"website": self.website,
				"territory": self.territory,
				"industry": self.industry,
				"annual_revenue": self.annual_revenue,
			}
		)
		customer.insert(ignore_permissions=True)
		return customer.name

	def contact_exists(self, throw=True):
		email_exist = frappe.db.exists("Contact Email", {"email_id": self.email_id})
		phone_exist = frappe.db.exists("Contact Phone", {"phone": self.phone})
		mobile_exist = frappe.db.exists("Contact Phone", {"phone": self.mobile_no})

		doctype = "Contact Email" if email_exist else "Contact Phone"
		name = email_exist or phone_exist or mobile_exist

		if name:
			text = "Email" if email_exist else "Phone" if phone_exist else "Mobile No"
			data = self.email_id if email_exist else self.phone if phone_exist else self.mobile_no

			value = "{0}: {1}".format(text, data)

			contact = frappe.db.get_value(doctype, name, "parent")

			if throw:
				frappe.throw(
					_("Contact already exists with {0}").format(value),
					title=_("Contact Already Exists"),
				)
			return contact

		return False

	def create_opportunity(self, contact, customer):
		from erpnext.crm.doctype.lead.lead import make_opportunity
		opportunity = make_opportunity(self.name)

		opportunity.update(
			{
				"contacts": [{"contact": contact}],
				"customer": customer
			}
		)

		if self.first_responded_on:
			opportunity.update(
				{
					"sla_creation": self.sla_creation,
					"response_by": self.response_by,
					"sla_status": self.sla_status,
					"communication_status": self.communication_status,
					"first_response_time": self.first_response_time,
					"first_responded_on": self.first_responded_on
				}
			)

		opportunity.insert(ignore_permissions=True)
		return opportunity.name

	def set_sla(self):
		"""
		Find an SLA to apply to the lead.
		"""
		if self.sla: return

		sla = get_sla(self)
		if not sla:
			self.first_responded_on = None
			self.first_response_time = None
			return
		self.sla = sla.name

	def apply_sla(self):
		"""
		Apply SLA if set.
		"""
		if not self.sla:
			return
		sla = frappe.get_last_doc("CRM Service Level Agreement", {"name": self.sla})
		if sla:
			sla.apply(self)

	def convert_to_opportunity(self):
		return convert_to_opportunity(lead=self.name, doc=self)

	@staticmethod
	def get_non_filterable_fields():
		return ["converted"]

	@staticmethod
	def default_list_data():
		columns = [
			{
				'label': 'Name',
				'type': 'Data',
				'key': 'lead_name',
				'width': '12rem',
			},
			{
				'label': 'Customer',
				'type': 'Link',
				'key': 'company_name',
				'options': 'Customer',
				'width': '10rem',
			},
			{
				'label': 'Status',
				'type': 'Select',
				'key': 'status',
				'width': '8rem',
			},
			{
				'label': 'Email',
				'type': 'Data',
				'key': 'email_id',
				'width': '12rem',
			},
			{
				'label': 'Mobile No',
				'type': 'Data',
				'key': 'mobile_no',
				'width': '11rem',
			},
			{
				'label': 'Assigned To',
				'type': 'Text',
				'key': '_assign',
				'width': '10rem',
			},
			{
				'label': 'Last Modified',
				'type': 'Datetime',
				'key': 'modified',
				'width': '8rem',
			},
		]
		rows = [
			"name",
			"lead_name",
			"customer",
			"status",
			"email_id",
			"mobile_no",
			"lead_owner",
			"first_name",
			"sla_status",
			"response_by",
			"first_response_time",
			"first_responded_on",
			"modified",
			"_assign",
			"image",
		]
		return {'columns': columns, 'rows': rows}

	@staticmethod
	def default_kanban_settings():
		return {
			"column_field": "status",
			"title_field": "lead_name",
			"kanban_fields": '["customer", "email_id", "mobile_no", "_assign", "modified"]'
		}


@frappe.whitelist()
def convert_to_opportunity(lead, doc=None):
	if not (doc and doc.flags.get("ignore_permissions")) and not frappe.has_permission("Lead", "write", lead):
		frappe.throw(_("Not allowed to convert Lead to Opportunity"), frappe.PermissionError)

	lead = frappe.get_cached_doc("Lead", lead)
	if frappe.db.exists("CRM Lead Status", "Qualified"):
		lead.status = "Qualified"
	lead.converted = 1
	if lead.sla and frappe.db.exists("CRM Communication Status", "Replied"):
		lead.communication_status = "Replied"
	lead.save(ignore_permissions=True)
	contact = lead.create_contact(False)
	customer = lead.create_customer()
	opportunity = lead.create_opportunity(contact, customer)
	return opportunity