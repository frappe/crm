import datetime
import frappe
import pytz
from frappe.utils import add_days, today, get_datetime


def sync_event_to_lead_appointment(doc, method=None):
	"""Sync Event to CRM Lead appointment date/time"""
	try:
		if (doc.reference_doctype == "CRM Lead" and 
			doc.reference_docname and 
			doc.starts_on):
			
			lead = frappe.get_doc("CRM Lead", doc.reference_docname)
			
			# Always sync appointment date/time when event is created for CRM Lead
			starts_on = get_datetime(doc.starts_on)
			lead.custom_appointment_date = starts_on.date()
			lead.custom_appointment_time = starts_on.time()
			lead.save(ignore_permissions=True)
			
			frappe.msgprint(f"Appointment date and time updated for {lead.lead_name}: {starts_on.strftime('%Y-%m-%d at %H:%M')}")
				
	except Exception as e:
		frappe.log_error(
			title="Event to Lead Sync Error",
			message=f"Error syncing event {doc.name} to lead: {str(e)}"
		)


def auto_mark_no_show():
	"""
	Cron job that runs at 6:30 PM daily to mark leads as No Show
	Changes sub_status from "Appointment" to "No Show" for Connected leads on current day
	"""
	try:
		# Get the No Show sub-status ID
		no_show_sub_status = "No Show"

		# Verify that No Show sub-status exists
		if not frappe.db.exists("CRM Lead Sub Status", no_show_sub_status):
			frappe.log_error(
				title="Auto No Show Error",
				message="No Show sub-status not found. Please create 'No Show' in CRM Lead Sub Status."
			)
			return

		# Find all leads with status=Connected and sub_status=Appointment for today
		today_date = today()

		leads_to_update = frappe.db.sql("""
			SELECT l.name, l.lead_name
			FROM `tabCRM Lead` l
			INNER JOIN `tabEvent` e ON e.reference_docname = l.name
			WHERE l.status = 'Connected'
			AND l.custom_sub_status = 'Appointment'
			AND e.reference_doctype = 'CRM Lead'
			AND DATE(e.starts_on) = %s
		""", (today_date,), as_dict=True)

		updated_count = 0

		for lead_data in leads_to_update:
			try:
				# Update the lead
				lead = frappe.get_doc("CRM Lead", lead_data.name)
				lead.custom_sub_status = no_show_sub_status
				lead.save(ignore_permissions=True)

				updated_count += 1

				frappe.logger().info(f"Auto-marked {lead_data.lead_name} ({lead_data.name}) as No Show")

			except Exception as e:
				frappe.log_error(
					title="Auto No Show Update Error",
					message=f"Error updating lead {lead_data.name} to No Show: {e!s}"
				)

		# Commit all changes
		frappe.db.commit()

		if updated_count > 0:
			frappe.logger().info(f"Auto No Show job completed. Updated {updated_count} leads to No Show status.")
		else:
			frappe.logger().info("Auto No Show job completed. No leads found to update.")

	except Exception as e:
		frappe.log_error(
			title="Auto No Show Cron Error",
			message=f"Error in auto_mark_no_show cron job: {e!s}"
		)