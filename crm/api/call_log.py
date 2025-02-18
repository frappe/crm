import frappe
from frappe import _
from crm.fcrm.doctype.crm_notification.crm_notification import notify_user


def on_status_change(doc, status):
	try:
		if status == "No Answer":
			lead = None
			try:
				dynamic_link = frappe.get_doc("Dynamic Link", {
					"link_doctype": "CRM Lead",
					"parent": doc.name,
					"parenttype": "CRM Call Log"
				})
				if not dynamic_link:
					return

				lead = frappe.get_doc("CRM Lead", {
					"name": dynamic_link.link_name
				})
			except Exception:
				pass

			assign_to = doc.receiver
			if not assign_to:
				return

			owner = "Administrator"
			try:
				owner_doc = frappe.get_doc("User", {
					"full_name": "hackajob Bot"
				})
				if owner_doc:
					owner = owner_doc.name
			except Exception:
				pass

			if lead:
				notify_user(
					{
						"owner": owner,
						"assigned_to": assign_to,
						"notification_type": "Task",
						"message": "You have a missed call from {0} {1} {2}".format(lead.first_name, lead.last_name, doc.to),
						"notification_text": "You have a missed call from {0} {1} {2}".format(lead.first_name, lead.last_name, doc.to),
						"reference_doctype": "CRM Call Log",
						"reference_docname": doc.name,
						"redirect_to_doctype": "CRM Lead",
						"redirect_to_docname": lead.name,
					}
				)
			else:
				notify_user(
					{
						"owner": owner,
						"assigned_to": assign_to,
						"notification_type": "Task",
						"message": "You have a missed call from {0}".format(doc.to),
						"notification_text": "You have a missed call from {0}".format(doc.to),
						"reference_doctype": "CRM Call Log",
						"reference_docname": doc.name,
						"redirect_to_doctype": "CRM Call Log",
						"redirect_to_docname": doc.name,
					}
				)
	except Exception:
		pass
