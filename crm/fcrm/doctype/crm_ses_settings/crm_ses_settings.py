import frappe
from frappe.model.document import Document


class CRMSESSettings(Document):
	def on_update(self):
		_sync_inbound_email_account(self)


def _sync_inbound_email_account(doc):
	"""Mirror inbound fields from CRM SES Settings onto the linked Email Account doc."""
	account_name = doc.get("inbound_email_account")
	if not account_name or not frappe.db.exists("Email Account", account_name):
		return

	ea = frappe.get_doc("Email Account", account_name)
	ea.enable_incoming = int(bool(doc.get("enable_incoming")))
	ea.default_incoming = int(bool(doc.get("default_incoming")))
	ea.append_to = doc.get("append_to") or "CRM Lead"
	ea.create_lead_from_incoming_email = int(bool(doc.get("create_lead_from_incoming_email")))
	ea.save(ignore_permissions=True)  # SYSTEM-INTERNAL: called from on_update after permission check
