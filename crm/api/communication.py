import frappe
from frappe import _

from crm.api.doc import get_assigned_users
from crm.fcrm.doctype.crm_notification.crm_notification import notify_user


def after_insert(doc, method):
	"""
	Notify assigned users when an email is received on a Lead or Deal.

	This hook is triggered after a Communication document is created.
	We only process incoming emails that are linked to CRM Lead or CRM Deal.
	"""
	if not (
		doc.communication_medium == "Email"
		and doc.sent_or_received == "Received"
	):
		return

	if doc.reference_doctype not in ["CRM Lead", "CRM Deal"]:
		return

	if not doc.reference_name:
		return

	notify_email_received(doc)


def notify_email_received(doc):
	"""
	Create notifications for all users assigned to the Lead/Deal.

	If the email is linked to a converted Lead, we notify the Deal assignees instead,
	since the Deal is now the active record for this customer.

	Args:
		doc: Communication document instance
	"""
	reference_doctype = doc.reference_doctype
	reference_name = doc.reference_name
	reference_doc = None

	if reference_doctype == "CRM Lead":
		try:
			reference_doc = frappe.get_doc("CRM Lead", reference_name)
			if reference_doc.converted:
				deal_name = frappe.db.get_value(
					"CRM Deal",
					{"lead": reference_name},
					"name",
					order_by="creation desc"
				)
				if deal_name:
					reference_doctype = "CRM Deal"
					reference_name = deal_name
					reference_doc = frappe.get_doc(reference_doctype, reference_name)
		except (frappe.DoesNotExistError, frappe.ValidationError):
			return
	else:
		try:
			reference_doc = frappe.get_doc(reference_doctype, reference_name)
		except (frappe.DoesNotExistError, frappe.ValidationError):
			return

	assigned_users = get_assigned_users(reference_doctype, reference_name)
	if not assigned_users:
		return

	doctype = reference_doctype
	if doctype and doctype.startswith("CRM "):
		doctype = doctype[4:].lower()

	if reference_doctype == "CRM Lead":
		display_name = reference_doc.lead_name or reference_name
	elif reference_doctype == "CRM Deal":
		display_name = (
			reference_doc.organization
			or reference_doc.lead_name
			or reference_name
		)
	else:
		display_name = reference_name

	sender_name = doc.sender_full_name or doc.sender or _("Someone")

	notification_text = f"""
		<div class="mb-2 leading-5 text-ink-gray-5">
			<span class="font-medium text-ink-gray-9">{sender_name}</span>
			<span>{_('sent an email to {0}').format(doctype)}</span>
			<span class="font-medium text-ink-gray-9">{display_name}</span>
		</div>
	"""

	message = doc.subject or _("No subject")

	for user in assigned_users:
		notify_user(
			{
				"owner": doc.owner,
				"assigned_to": user,
				"notification_type": "Email",
				"message": message,
				"notification_text": notification_text,
				"reference_doctype": "Communication",
				"reference_docname": doc.name,
				"redirect_to_doctype": reference_doctype,
				"redirect_to_docname": reference_name,
			}
		)
