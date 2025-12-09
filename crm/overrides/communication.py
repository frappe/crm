# Copyright (c) 2024, Custom Zip ERP and contributors
# For license information, please see license.txt

import frappe
from frappe.core.doctype.communication.communication import Communication
from frappe.utils import get_formatted_email
from frappe.email.doctype.email_account.email_account import EmailAccount


class CustomCommunication(Communication):
	"""Override Communication to use FROM field selection or custom_reply_email_alias from CRM Lead and HD Ticket"""

	def mail_sender(self):
		"""Override to use email_account (FROM field) first, then custom_reply_email_alias, then default"""
		# PRIORITY 1: If email_account is set (FROM field was used), use that email account's email_id
		if self.email_account:
			try:
				email_account = EmailAccount.find(self.email_account)
				if email_account and email_account.email_id:
					return email_account.email_id
			except Exception:
				pass
		
		# PRIORITY 2: Use custom_reply_email_alias from CRM Lead or HD Ticket (stored from initial routing)
		if self.reference_doctype == "CRM Lead" and self.reference_name:
			try:
				lead = frappe.get_cached_doc("CRM Lead", self.reference_name)
				if lead.get("custom_reply_email_alias"):
					return lead.custom_reply_email_alias
			except Exception:
				pass
		
		if self.reference_doctype == "HD Ticket" and self.reference_name:
			try:
				ticket = frappe.get_cached_doc("HD Ticket", self.reference_name)
				if ticket.get("custom_reply_email_alias"):
					return ticket.custom_reply_email_alias
			except Exception:
				pass
		
		# PRIORITY 3: Fall back to parent class method (default behavior)
		return super().mail_sender()

	def get_mail_sender_with_displayname(self):
		"""Override to use email_account (FROM field) first, then alias, then default"""
		# PRIORITY 1: If email_account is set (FROM field was used), use that
		if self.email_account:
			try:
				email_account = EmailAccount.find(self.email_account)
				if email_account and email_account.email_id:
					sender_name = self.mail_sender_fullname()
					return get_formatted_email(sender_name, mail=email_account.email_id)
			except Exception:
				pass
		
		# PRIORITY 2: Use custom_reply_email_alias from Lead/Ticket
		if self.reference_doctype == "CRM Lead" and self.reference_name:
			try:
				lead = frappe.get_cached_doc("CRM Lead", self.reference_name)
				if lead.get("custom_reply_email_alias"):
					sender_name = self.mail_sender_fullname()
					return get_formatted_email(sender_name, mail=lead.custom_reply_email_alias)
			except Exception:
				pass
		
		if self.reference_doctype == "HD Ticket" and self.reference_name:
			try:
				ticket = frappe.get_cached_doc("HD Ticket", self.reference_name)
				if ticket.get("custom_reply_email_alias"):
					sender_name = self.mail_sender_fullname()
					return get_formatted_email(sender_name, mail=ticket.custom_reply_email_alias)
			except Exception:
				pass
		
		# PRIORITY 3: Fall back to parent class method
		return super().get_mail_sender_with_displayname()

	def sendmail_input_dict(self, *args, **kwargs):
		"""Override to set reply_to and sender - FROM field takes priority over alias"""
		input_dict = super().sendmail_input_dict(*args, **kwargs)
		
		sender_email = None
		
		# PRIORITY 1: If email_account is set (FROM field was used), use that
		if self.email_account:
			try:
				email_account = EmailAccount.find(self.email_account)
				if email_account and email_account.email_id:
					sender_email = email_account.email_id
			except Exception:
				pass
		
		# PRIORITY 2: If no FROM field selection, use custom_reply_email_alias from Lead/Ticket
		if not sender_email:
			if self.reference_doctype == "CRM Lead" and self.reference_name:
				try:
					lead = frappe.get_cached_doc("CRM Lead", self.reference_name)
					if lead.get("custom_reply_email_alias"):
						sender_email = lead.custom_reply_email_alias
				except Exception:
					pass
			
			if not sender_email and self.reference_doctype == "HD Ticket" and self.reference_name:
				try:
					ticket = frappe.get_cached_doc("HD Ticket", self.reference_name)
					if ticket.get("custom_reply_email_alias"):
						sender_email = ticket.custom_reply_email_alias
				except Exception:
					pass
		
		# If we have a sender email (from FROM field or alias), set it
		if sender_email:
			input_dict["reply_to"] = sender_email
			sender_name = self.mail_sender_fullname()
			input_dict["sender"] = get_formatted_email(sender_name, mail=sender_email)
		
		return input_dict

