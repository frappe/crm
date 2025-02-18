import frappe
from frappe import _
from crm.fcrm.doctype.crm_notification.crm_notification import notify_user


def before_insert(doc, method):
	if doc.sent_or_received != "Received" or doc.communication_medium != "Email":
		return

	if doc.reference_doctype is not None or doc.reference_name is not None:
		return

	lead = frappe.get_all("CRM Lead", filters={"email": doc.sender}, fields=["name"])
	if not lead:
		return

	doc.reference_doctype = "CRM Lead"
	doc.reference_name = lead[0].name


def after_insert(doc, method):
	try:
		if doc.reference_doctype != "CRM Lead" or not doc.reference_name:
			return

		if not doc.email_account:
			return

		lead = frappe.get_doc("CRM Lead", {
			"name": doc.reference_name
		})

		email_account = frappe.get_doc("Email Account", doc.email_account)
		email_account_email_id = email_account.email_id
		assign_to = frappe.get_doc("User", {
			"email": email_account_email_id
		})

		owner = "Administrator"
		try:
			owner_doc = frappe.get_doc("User", {
				"full_name": "hackajob Bot"
			})
			if owner_doc:
				owner = owner_doc.name
		except Exception:
			pass

		notify_user(
			{
				"owner": owner,
				"assigned_to": assign_to.name,
				"notification_type": "Task",
				"message": "You received an email from {0} {1} {2}".format(lead.first_name, lead.last_name, doc.sender),
				"notification_text": "You received an email from {0} {1} {2}".format(lead.first_name, lead.last_name, doc.sender),
				"reference_doctype": "Communication",
				"reference_docname": doc.name,
				"redirect_to_doctype": "CRM Lead",
				"redirect_to_docname": doc.reference_name,
			}
		)
	except Exception:
		pass
