import frappe
from frappe import _


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
			frappe.set_user(owner)

			if lead:
				message = "You have a missed call from {0} {1} {2}".format(lead.first_name, lead.last_name, doc.to)
				start_date = frappe.utils.now_datetime()
				values = frappe._dict(
					doctype="CRM Task",
					assigned_to=assign_to,
					title=message,
					description=message,
					priority="Medium",
					start_date=start_date,
					reference_doctype="CRM Lead",
					reference_docname=lead.name
				)
				frappe.get_doc(values).insert(ignore_permissions=True)
			else:
				message = "You have a missed call from {0}".format(doc.to)
				start_date = frappe.utils.now_datetime()
				values = frappe._dict(
					doctype="CRM Task",
					assigned_to=assign_to,
					title=message,
					description=message,
					priority="Medium",
					start_date=start_date
				)
				frappe.get_doc(values).insert(ignore_permissions=True)
	except Exception as e:
		pass
