import frappe
from frappe import _


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
		frappe.set_user(owner)

		message = "You received an email from {0} {1} {2}".format(lead.first_name, lead.last_name, doc.sender)
		start_date = frappe.utils.now_datetime()
		values = frappe._dict(
			doctype="CRM Task",
			assigned_to=assign_to.name,
			title=message,
			description="Subject: {0}<br />Content:<br />{1}".format(doc.subject, doc.content),
			priority="Medium",
			start_date=start_date,
			reference_doctype="CRM Lead",
			reference_docname=doc.reference_name
		)
		frappe.get_doc(values).insert(ignore_permissions=True)
	except Exception as e:
		pass
