# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from frappe.utils import has_gravatar, validate_email_address


class CRMLead(Document):
	def validate(self):
		self.set_full_name()
		self.set_lead_name()
		self.set_title()
		self.validate_email()

	def set_full_name(self):
		if self.first_name:
			self.lead_name = " ".join(
				filter(None, [self.salutation, self.first_name, self.middle_name, self.last_name])
			)

	def set_lead_name(self):
		if not self.lead_name:
			# Check for leads being created through data import
			if not self.organization and not self.email and not self.flags.ignore_mandatory:
				frappe.throw(_("A Lead requires either a person's name or an organization's name"))
			elif self.organization:
				self.lead_name = self.organization
			elif self.email:
				self.lead_name = self.email.split("@")[0]
			else:
				self.lead_name = "Unnamed Lead"

	def set_title(self):
		self.title = self.organization or self.lead_name

	def validate_email(self):
		if self.email:
			if not self.flags.ignore_email_validation:
				validate_email_address(self.email, throw=True)

			if self.email == self.lead_owner:
				frappe.throw(_("Lead Owner cannot be same as the Lead Email Address"))

			if self.is_new() or not self.image:
				self.image = has_gravatar(self.email)

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
				"company_name": self.organization,
				"image": self.image or "",
			}
		)

		if self.email:
			contact.append("email_ids", {"email_id": self.email, "is_primary": 1})

		if self.phone:
			contact.append("phone_nos", {"phone": self.phone, "is_primary_phone": 1})

		if self.mobile_no:
			contact.append("phone_nos", {"phone": self.mobile_no, "is_primary_mobile_no": 1})

		contact.insert(ignore_permissions=True)
		contact.reload()  # load changes by hooks on contact

		return contact.name

	def contact_exists(self, throw=True):
		email_exist = frappe.db.exists("Contact Email", {"email_id": self.email})
		phone_exist = frappe.db.exists("Contact Phone", {"phone": self.phone})
		mobile_exist = frappe.db.exists("Contact Phone", {"phone": self.mobile_no})

		doctype = "Contact Email" if email_exist else "Contact Phone"
		name = email_exist or phone_exist or mobile_exist

		if name:
			text = "Email" if email_exist else "Phone" if phone_exist else "Mobile No"
			data = self.email if email_exist else self.phone if phone_exist else self.mobile_no

			value = "{0}: {1}".format(text, data)

			contact = frappe.db.get_value(doctype, name, "parent")

			if throw:
				frappe.throw(
					_("Contact already exists with {0}").format(value),
					title=_("Contact Already Exists"),
				)
			return contact

		return False

	def create_deal(self, contact):
		deal = frappe.new_doc("CRM Deal")
		deal.update(
			{
				"lead": self.name,
				"organization": self.organization,
				"deal_owner": self.lead_owner,
				"contacts": [{"contact": contact}],
			}
		)
		deal.insert(ignore_permissions=True)
		return deal.name

	@staticmethod
	def sort_options():
		return [
			{ "label": 'Created', "value": 'creation' },
			{ "label": 'Modified', "value": 'modified' },
			{ "label": 'Status', "value": 'status' },
			{ "label": 'Lead owner', "value": 'lead_owner' },
			{ "label": 'Organization', "value": 'organization' },
			{ "label": 'Name', "value": 'lead_name' },
			{ "label": 'First Name', "value": 'first_name' },
			{ "label": 'Last Name', "value": 'last_name' },
			{ "label": 'Email', "value": 'email' },
			{ "label": 'Mobile no', "value": 'mobile_no' },
		]

	@staticmethod
	def default_list_data():
		columns = [
			{
				'label': 'Name',
				'key': 'lead_name',
				'width': '12rem',
			},
			{
				'label': 'Organization',
				'key': 'organization',
				'width': '10rem',
			},
			{
				'label': 'Status',
				'key': 'status',
				'width': '8rem',
			},
			{
				'label': 'Email',
				'key': 'email',
				'width': '12rem',
			},
			{
				'label': 'Mobile no',
				'key': 'mobile_no',
				'width': '11rem',
			},
			{
				'label': 'Lead owner',
				'key': 'lead_owner',
				'width': '10rem',
			},
			{
				'label': 'Last modified',
				'key': 'modified',
				'width': '8rem',
			},
		]
		data_fields = ['name', 'first_name', 'image']
		return {'columns': columns, 'data_fields': data_fields}

@frappe.whitelist()
def convert_to_deal(lead):
	if not frappe.has_permission("CRM Lead", "write", lead):
		frappe.throw(_("Not allowed to convert Lead to Deal"), frappe.PermissionError)

	lead = frappe.get_cached_doc("CRM Lead", lead)
	lead.status = "Qualified"
	lead.converted = 1
	contact = lead.create_contact(False)
	deal = lead.create_deal(contact)
	lead.save()
	return deal