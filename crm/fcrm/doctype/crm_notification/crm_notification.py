# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from crm.overrides.notification_log import send_notification_email

class CRMNotification(Document):
	def on_update(self):
		frappe.publish_realtime("crm_notification")
	
	def after_insert(self):
		self.send_mail_to_self_assigned_contact()
		
	#send mail if contact is self assigned
	def send_mail_to_self_assigned_contact(self):
		if self.from_user == self.to_user and self.reference_doctype == "Contact" :
			notification = frappe.new_doc("Notification Log")
			notification.for_user = self.to_user
			notification.from_user = self.from_user
			notification.document_type = self.reference_doctype
			notification.document_name = self.reference_name
			notification.subject = self.message
			notification.type = "Assignment"
			notification.message = self.reference_name
			notification.insert(ignore_permissions=True)
		
def notify_user(args):
	"""
	Notify the assigned user
	"""
	args = frappe._dict(args)
	
	'''Applied condition that owner is same assigned user then 
	it can allow to create CRM notification for Contact '''
	if args.reference_doctype != 'Contact':
		if args.owner == args.assigned_to:
			return

	values = frappe._dict(
		doctype="CRM Notification",
		from_user=args.owner,
		to_user=args.assigned_to,
		type=args.notification_type,
		message=args.message,
		notification_text=args.notification_text,
		notification_type_doctype=args.reference_doctype,
		notification_type_doc=args.reference_docname,
		reference_doctype=args.redirect_to_doctype,
		reference_name=args.redirect_to_docname,
	)
	if frappe.db.exists("CRM Notification", values):
		return
	frappe.get_doc(values).insert(ignore_permissions=True)



