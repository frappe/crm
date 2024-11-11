# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import json

import frappe
from frappe import _
from frappe.desk.form.assign_to import add as assign

from erpnext.crm.doctype.lead.lead import Lead
from crm.fcrm.doctype.crm_service_level_agreement.utils import get_sla
from crm.fcrm.doctype.crm_status_change_log.crm_status_change_log import add_status_change_log


class Lead(Lead):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from erpnext.crm.doctype.crm_note.crm_note import CRMNote
		from frappe.types import DF

		annual_revenue: DF.Currency
		blog_subscriber: DF.Check
		campaign_name: DF.Link | None
		city: DF.Data | None
		company: DF.Link | None
		company_name: DF.Data | None
		country: DF.Link | None
		customer: DF.Link | None
		disabled: DF.Check
		email_id: DF.Data | None
		fax: DF.Data | None
		first_name: DF.Data | None
		gender: DF.Link | None
		image: DF.AttachImage | None
		industry: DF.Link | None
		job_title: DF.Data | None
		language: DF.Link | None
		last_name: DF.Data | None
		lead_name: DF.Data | None
		lead_owner: DF.Link | None
		market_segment: DF.Link | None
		middle_name: DF.Data | None
		mobile_no: DF.Data | None
		naming_series: DF.Literal["CRM-LEAD-.YYYY.-"]
		no_of_employees: DF.Literal["1-10", "11-50", "51-200", "201-500", "501-1000", "1000+"]
		notes: DF.Table[CRMNote]
		phone: DF.Data | None
		phone_ext: DF.Data | None
		qualification_status: DF.Literal["Unqualified", "In Process", "Qualified"]
		qualified_by: DF.Link | None
		qualified_on: DF.Date | None
		request_type: DF.Literal["", "Product Enquiry", "Request for Information", "Suggestions", "Other"]
		salutation: DF.Link | None
		source: DF.Link | None
		state: DF.Data | None
		status: DF.Literal["Lead", "Open", "Replied", "Opportunity", "Quotation", "Lost Quotation", "Interested", "Converted", "Do Not Contact"]
		territory: DF.Link | None
		title: DF.Data | None
		type: DF.Literal["", "Client", "Channel Partner", "Consultant"]
		unsubscribed: DF.Check
		website: DF.Data | None
		whatsapp_no: DF.Data | None
	# end: auto-generated types
	def before_validate(self):
		self.set_sla()
		super()

	def validate(self):
		super()
		if not self.is_new() and self.has_value_changed("lead_owner") and self.lead_owner:
			self.share_with_agent(self.lead_owner)
			self.assign_agent(self.lead_owner)
		# if self.has_value_changed("status"):
		# 	add_status_change_log(self)

	def after_insert(self):
		if self.lead_owner:
			self.assign_agent(self.lead_owner)
		super()

	def before_save(self):
		self.apply_sla()
		super()

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

	def create_contact(self, throw=True):
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
		if not self.customer:
			return

		existing_customer = frappe.db.exists("Customer", {"customer_name": self.customer})
		if existing_customer:
			return existing_customer

		customer = frappe.new_doc("Customer")
		customer.update(
			{
				"customer_name": self.customer,
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
		opportunity = frappe.new_doc("Opportunity")

		lead_opportunity_map = {
			"lead_owner": "opportunity_owner",
		}

		restricted_fieldtypes = ["Tab Break", "Section Break", "Column Break", "HTML", "Button", "Attach", "Table"]
		restricted_map_fields = ["name", "naming_series", "creation", "owner", "modified", "modified_by", "idx", "docstatus", "status", "email_id", "mobile_no", "phone", "sla", "sla_status", "response_by", "first_response_time", "first_responded_on", "communication_status", "sla_creation"]

		for field in self.meta.fields:
			if field.fieldtype in restricted_fieldtypes:
				continue
			if field.fieldname in restricted_map_fields:
				continue

			fieldname = field.fieldname
			if field.fieldname in lead_opportunity_map:
				fieldname = lead_opportunity_map[field.fieldname]

			if hasattr(opportunity, fieldname):
				if fieldname == "customer":
					opportunity.update({fieldname: customer})
				else:
					opportunity.update({fieldname: self.get(field.fieldname)})

		opportunity.update(
			{
				"opportunity_from": "lead",
				"party_name": self.name,
				"contacts": [{"contact": contact}],
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
				'key': 'customer',
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