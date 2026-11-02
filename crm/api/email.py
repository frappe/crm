import frappe
from frappe import _


@frappe.whitelist()
def cancel_scheduled_email(name: str):
	"""Cancel a scheduled email before it goes out and return it as a draft.

	Deletes the queued email and its Communication. The returned attachments are the
	files still attached to the lead/deal, so the draft can be sent again with them.
	"""
	communication, queues = get_scheduled_email(name)

	file_urls = frappe.get_all(
		"File",
		filters={"attached_to_doctype": "Communication", "attached_to_name": name},
		pluck="file_url",
	)
	attachments = (
		frappe.get_all(
			"File",
			filters={
				"attached_to_doctype": communication.reference_doctype,
				"attached_to_name": communication.reference_name,
				"file_url": ["in", file_urls],
			},
			fields=["name", "file_name", "file_url"],
		)
		if file_urls
		else []
	)

	for queue in queues:
		frappe.delete_doc("Email Queue", queue, ignore_permissions=True)
	communication.delete(ignore_permissions=True)

	return {
		"subject": communication.subject,
		"content": communication.content,
		"sender": communication.sender,
		"recipients": communication.recipients,
		"cc": communication.cc,
		"bcc": communication.bcc,
		"attachments": attachments,
	}


@frappe.whitelist()
def send_scheduled_email_now(name: str):
	"""Send a scheduled email right away instead of at its scheduled time."""
	communication, queues = get_scheduled_email(name)

	communication.db_set({"send_after": None, "delivery_status": "Sending"})
	for queue in queues:
		frappe.db.set_value("Email Queue", queue, "send_after", None)
		# Same as sending with `now`; if it can't go out here, the queue retries it
		frappe.get_doc("Email Queue", queue).send()


def get_scheduled_email(name: str):
	"""Return the Communication and its queued emails, if it's still waiting to be sent."""
	communication = frappe.get_doc("Communication", name)

	if communication.owner != frappe.session.user:
		frappe.throw(_("You can only change emails you scheduled"), frappe.PermissionError)

	if communication.delivery_status != "Scheduled":
		frappe.throw(_("This email is no longer scheduled"))

	# Lock the queue rows so the scheduler can't pick them up while we change them
	EmailQueue = frappe.qb.DocType("Email Queue")
	queues = (
		frappe.qb.from_(EmailQueue)
		.select(EmailQueue.name, EmailQueue.status)
		.where(EmailQueue.communication == name)
		.for_update()
		.run(as_dict=True)
	)
	if any(q.status != "Not Sent" for q in queues):
		frappe.throw(_("This email is already being sent"))

	return communication, [q.name for q in queues]
