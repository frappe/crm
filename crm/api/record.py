import frappe
from frappe import _
from frappe.desk.form.assign_to import set_status
from frappe.model.delete_doc import get_dynamic_linked_docs, get_linked_docs

from crm.fcrm.doctype.crm_fields_layout.crm_fields_layout import get_permlevel_access


@frappe.whitelist(methods=["GET"])
def get_assignees(doctype: str, name: str | int) -> list[str]:
	"""Return the users assigned to a record.

	doctype: the record's DocType.
	name: the record's name.
	"""
	frappe.get_doc(doctype, name).check_permission("read")
	return get_open_assignees(doctype, name)


@frappe.whitelist(methods=["GET"])
def get_activities(doctype: str, name: str | int) -> dict[str, list[dict]]:
	"""Return a record's timeline, notes, tasks and attachments.

	The timeline holds field changes, comments, emails, attachment logs and notes.
	doctype: the record's DocType.
	name: the record's name.
	"""
	# crm.api.activities imports this module at load time
	from crm.api.activities import get_record_activities

	doc = frappe.get_doc(doctype, name)
	doc.check_permission("read")
	return get_record_activities(doc)


@frappe.whitelist(methods=["POST"])
def update_record(doctype: str, name: str | int, values: dict, modified: str) -> str:
	"""Save values on a record unless it changed after the caller read it.

	Returns the record's new `modified`. Raises frappe.TimestampMismatchError
	when the record was saved after `modified`.
	doctype: the record's DocType.
	name: the record's name.
	values: the fields to change, by fieldname; standard, read-only and unknown fields are refused.
	modified: the record's `modified` timestamp when the caller read it.
	"""
	check_fields_are_writable(doctype, values)
	doc = frappe.get_doc(doctype, name)
	doc.update(values)
	# save() compares this with the stored value and raises TimestampMismatchError
	doc.modified = modified
	doc.save()
	return doc.modified


@frappe.whitelist(methods=["POST"])
def remove_assignees(doctype: str, name: str | int, assignees: list[str]) -> None:
	"""Remove users from a record's assignees.

	doctype: the record's DocType.
	name: the record's name.
	assignees: the users to remove.
	"""
	for assignee in assignees:
		set_status(doctype, name, todo=None, assign_to=assignee, status="Cancelled")


@frappe.whitelist(methods=["POST"])
def mark_as_seen(doctype: str, name: str | int) -> None:
	"""Mark a record as seen and viewed by the current user.

	doctype: the record's DocType.
	name: the record's name.
	"""
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("read")
	doc.add_seen()
	doc.add_viewed()


@frappe.whitelist(methods=["GET"])
def get_linked_records(doctype: str, name: str | int) -> list[dict]:
	"""Return the records that link to a record and that the user can read.

	doctype: the record's DocType.
	name: the record's name.
	"""
	try:
		doc = frappe.get_doc(doctype, name)
	except frappe.DoesNotExistError:
		return []

	doc.check_permission("read")
	return [
		d
		for d in get_linked_docs_data(doc)
		if frappe.has_permission(d["reference_doctype"], "read", d["reference_docname"])
	]


@frappe.whitelist(methods=["POST"])
def unlink_records(records: list[dict], remove_contact: bool = False, delete: bool = False) -> list[dict]:
	"""Unlink each record from its parent, delete it if asked, and return those done.

	records: the records to unlink, each a dict with "doctype" and "docname".
	remove_contact: clear the records' contact instead of their reference.
	delete: also delete each record after it is unlinked.
	"""
	# crm.api.whatsapp imports this module at load time
	from crm.api.whatsapp import WhatsAppRecipientChangeError

	unlinked = []
	for item in records:
		if not item.get("doctype") or not item.get("docname"):
			continue

		if not frappe.has_permission(item["doctype"], "write", item["docname"]):
			continue

		remove_link = remove_contact_link if remove_contact else remove_doc_link
		try:
			is_unlinked = remove_link(item["doctype"], item["docname"])
			if delete:
				frappe.delete_doc(item["doctype"], item["docname"])
		except WhatsAppRecipientChangeError:
			raise
		except (frappe.DoesNotExistError, frappe.ValidationError):
			continue

		if is_unlinked or delete:
			unlinked.append({"doctype": item["doctype"], "docname": item["docname"]})

	return unlinked


@frappe.whitelist(methods=["POST"])
def delete_records(doctype: str, names: list[str | int], delete_linked: bool = False) -> None:
	"""Delete records and unlink, or delete, the records that link to them.

	More than 10 records are deleted in a background job.
	doctype: the records' DocType.
	names: the names of the records to delete.
	delete_linked: delete the linked records instead of unlinking them.
	"""
	from frappe.desk.reportview import delete_bulk

	if not doctype:
		frappe.throw(_("Doctype is required"))

	if not names:
		frappe.throw(_("Names are required"))

	for name in names:
		if frappe.db.exists(doctype, name):
			frappe.get_doc(doctype, name).check_permission("delete")

	for name in names:
		unlink_records_linked_to(doctype, name, delete_linked)

	if len(names) > 10:
		frappe.enqueue("frappe.desk.reportview.delete_bulk", doctype=doctype, items=names)
	else:
		delete_bulk(doctype, names)


def check_fields_are_writable(doctype: str, fieldnames) -> None:
	"""Refuse anything but fields the user may edit, such as `name` or `__islocal`."""
	meta = frappe.get_meta(doctype)
	write_levels = get_permlevel_access("write", doctype)
	refused = sorted(
		fieldname
		for fieldname in fieldnames
		if not (field := meta.get_field(fieldname)) or field.read_only or field.permlevel not in write_levels
	)
	if refused:
		frappe.throw(_("Cannot edit these fields of {0}: {1}").format(_(doctype), ", ".join(refused)))


def unlink_records_linked_to(doctype, name, delete_linked):
	try:
		if not frappe.db.exists(doctype, name):
			frappe.log_error(f"Document {doctype} {name} does not exist", "Bulk Delete Error")
			return

		for linked_doc in get_linked_docs_data(frappe.get_doc(doctype, name)):
			unlink_records(
				[{"doctype": linked_doc["reference_doctype"], "docname": linked_doc["reference_docname"]}],
				remove_contact=doctype == "Contact",
				delete=delete_linked,
			)
	except Exception as e:
		frappe.log_error(f"Error processing linked docs for {doctype} {name}: {e!s}", "Bulk Delete Error")


def get_open_assignees(doctype, name, default_assigned_to=None):
	assigned_users = frappe.get_all(
		"ToDo",
		fields=["allocated_to"],
		filters={
			"reference_type": doctype,
			"reference_name": name,
			"status": ("not in", ("Closed", "Cancelled")),
		},
		pluck="allocated_to",
	)

	users = list(set(assigned_users))
	if not users and default_assigned_to:
		users = [default_assigned_to]
	return users


def get_linked_docs_data(doc):
	linked_docs = get_linked_docs(doc)
	dynamic_linked_docs = get_dynamic_linked_docs(doc)

	linked_docs.extend(dynamic_linked_docs)
	linked_docs = list({doc["reference_docname"]: doc for doc in linked_docs}.values())

	docs_data = []
	for doc in linked_docs:
		if not doc.get("reference_doctype") or not doc.get("reference_docname"):
			continue

		try:
			data = frappe.get_doc(doc["reference_doctype"], doc["reference_docname"])
		except (frappe.DoesNotExistError, frappe.ValidationError):
			continue

		title = data.get("title")
		if data.doctype == "CRM Call Log":
			title = f"Call from {data.get('from')} to {data.get('to')}"

		if data.doctype == "CRM Deal":
			title = data.get("organization")

		if data.doctype == "CRM Notification":
			title = data.get("message")

		docs_data.append(
			{
				"doc": data.doctype,
				"title": title or data.get("name"),
				"reference_docname": doc["reference_docname"],
				"reference_doctype": doc["reference_doctype"],
			}
		)
	return docs_data


def remove_doc_link(doctype, docname):
	if not doctype or not docname:
		return False

	try:
		linked_doc_data = frappe.get_doc(doctype, docname)
		if doctype == "CRM Notification":
			delete_notification_type = {
				"notification_type_doctype": "",
				"notification_type_doc": "",
			}
			delete_references = {
				"reference_doctype": "",
				"reference_name": "",
			}

			if linked_doc_data.get("notification_type_doctype") == linked_doc_data.get("reference_doctype"):
				delete_references.update(delete_notification_type)

			linked_doc_data.update(delete_references)
		else:
			linked_doc_data.update(
				{
					"reference_doctype": "",
					"reference_docname": "",
				}
			)
		linked_doc_data.save(ignore_permissions=True)
		return True
	except (frappe.DoesNotExistError, frappe.ValidationError):
		return False


def remove_contact_link(doctype, docname):
	# crm.api.whatsapp imports this module at load time
	from crm.api.whatsapp import WhatsAppRecipientChangeError

	if not doctype or not docname:
		return False

	try:
		linked_doc_data = frappe.get_doc(doctype, docname)
		linked_doc_data.update(
			{
				"contact": None,
				"contacts": [],
			}
		)
		linked_doc_data.save(ignore_permissions=True)
		return True
	except WhatsAppRecipientChangeError:
		raise
	except (frappe.DoesNotExistError, frappe.ValidationError):
		return False
