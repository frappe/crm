import frappe
from frappe import _
from crm.fcrm.doctype.crm_notification.crm_notification import notify_user

def schedule_task_notifications():
	#fetch all task whose due date is today
	task_data= frappe.db.sql(f"""
		select name, status, due_date, title, creation,assigned_to, owner 
		from `tabCRM Task` where status != 'Done' and status != 'Canceled'
		and due_date != 'NULL' and task_overdue_notification_sent = 0
		and DATE_ADD(due_date, INTERVAL 60 SECOND) <= NOW();""",as_dict=1)
	
	if task_data and len(task_data) > 0:
		for task in task_data:
			if frappe.db.exists("CRM Task", task['name']):
				create_crm_notification(task)
					 
def create_crm_notification(doc):
	due_date = doc['due_date'].strftime("%Y-%m-%d %H:%M:00")
	notify_user({
		"owner": doc.owner,
		"assigned_to": doc.assigned_to,
		"notification_type": "Task",
		"message": _(f"Task '{doc.title}' has exceeded Due Date {due_date}. Please take necessary action."),
		"notification_text": f"Task Due for {doc.title}",
		"reference_doctype": "CRM Task",
		"reference_docname": doc.name,
		"redirect_to_doctype": doc.reference_doctype,
		"redirect_to_docname": doc.reference_docname
	})
	frappe.db.set_value("CRM Task", doc.name, 'task_overdue_notification_sent', 1)