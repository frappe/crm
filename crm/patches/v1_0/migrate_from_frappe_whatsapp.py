import mimetypes

import frappe
from frappe.utils import strip_html_tags
from frappe.utils.password import get_decrypted_password
from whatsapp.whatsapp.api.utils import HEADER_TYPES, TEMPLATE_TYPES, get_template_variables
from whatsapp.whatsapp.doctype.wa_profile.wa_profile import get_or_create_profile
from whatsapp.whatsapp.doctype.wa_template.wa_template import _ensure_language

from crm.patches.v1_0.link_existing_whatsapp_profiles_to_crm import execute as link_profiles_to_crm

OLD_ACCOUNT = "WhatsApp Account"
OLD_SETTINGS = "WhatsApp Settings"
OLD_TEMPLATE = "WhatsApp Templates"
OLD_MESSAGE = "WhatsApp Message"

OUTGOING_STATUS = {
	"success": "Sent",
	"sent": "Sent",
	"delivered": "Delivered",
	"read": "Read",
	"failed": "Failed",
}
TEMPLATE_STATUS = {"APPROVED": "Approved", "REJECTED": "Rejected", "DELETED": "Deleted"}
TEMPLATE_TYPE = {**TEMPLATE_TYPES, "TRANSACTIONAL": "Utility", "OTP": "Authentication"}

REFERENCING_ROWS = (
	("File", "attached_to_doctype"),
	("Comment", "reference_doctype"),
	("CRM Notification", "notification_type_doctype"),
)


def execute():
	"""Copy a site's frappe_whatsapp data into the whatsapp app's DocTypes.

	The whatsapp app's rename patches skip DocTypes another app owns, so a CRM site
	coming from frappe_whatsapp gets empty WA tables. Messages keep their names so the
	rows that point at them only need the DocType swapped, and inserts bypass the
	controllers so nothing is re-sent to Meta. Templates are copied thinly; the daily
	sync fills in buttons and variables from Meta.
	"""
	if not frappe.db.exists("DocType", OLD_MESSAGE):
		return

	for account in frappe.get_all(OLD_ACCOUNT, fields=["*"]):
		_copy_account(account)
	_copy_settings()

	templates = {t.name: _copy_template(t) for t in frappe.get_all(OLD_TEMPLATE, fields=["*"])}

	old_messages = frappe.get_all(OLD_MESSAGE, fields=["*"], order_by="creation asc")
	for message in old_messages:
		if not frappe.db.exists("WA Message", message.name):
			_copy_message(message, templates)

	for doctype, fieldname in REFERENCING_ROWS:
		frappe.db.set_value(doctype, {fieldname: OLD_MESSAGE}, fieldname, "WA Message", update_modified=False)

	frappe.clear_cache()
	link_profiles_to_crm()


def _copy_account(old) -> None:
	if frappe.db.exists("WA Account", old.name):
		return
	frappe.get_doc(
		doctype="WA Account",
		account_name=old.account_name,
		status=old.status,
		app_id=old.app_id,
		business_id=old.business_id,
		phone_id=old.phone_id,
		auto_read_receipts=old.allow_auto_read_receipt,
		access_token=get_decrypted_password(OLD_ACCOUNT, old.name, "token", raise_exception=False),
	).insert(ignore_permissions=True)


def _copy_settings() -> None:
	default_account = frappe.db.get_single_value(OLD_SETTINGS, "default_outgoing_account")
	if not default_account:
		return
	account = frappe.db.get_value(
		OLD_ACCOUNT, default_account, ["url", "version", "webhook_verify_token"], as_dict=True
	)
	settings = frappe.get_single("WA Settings")
	settings.default_account = default_account
	settings.whatsapp_api_url = account.url or settings.whatsapp_api_url
	settings.whatsapp_api_version = account.version or settings.whatsapp_api_version
	settings.webhook_verify_token = account.webhook_verify_token
	settings.save(ignore_permissions=True)


def _copy_template(old) -> str:
	template_name = old.actual_name or old.template_name
	language = old.language_code or old.language
	_ensure_language(language)

	existing = frappe.db.get_value(
		"WA Template",
		{"template_name": template_name, "language": language, "whatsapp_account": old.whatsapp_account},
	)
	if existing:
		return existing

	doc = frappe.get_doc(
		doctype="WA Template",
		template_label=old.template_name,
		template_name=template_name,
		whatsapp_template_id=old.id,
		status=TEMPLATE_STATUS.get(old.status, "Pending"),
		template_type=TEMPLATE_TYPE.get(old.category, "Utility"),
		language=language,
		message=old.template,
		header_type=HEADER_TYPES.get(old.header_type, "Text"),
		header_text=old.header,
		footer=old.footer,
		whatsapp_account=old.whatsapp_account,
		variable_format="Positional",
		template_variables=_template_variables(old),
	)
	doc.flags.from_sync = True
	doc.insert(ignore_permissions=True)
	return doc.name


def _template_variables(old) -> list[dict]:
	"""The old app kept body examples as one comma-separated string in placeholder order."""
	examples = old.sample_values.split(",") if old.sample_values else []
	rows = {
		name: examples[index].strip() if index < len(examples) else name
		for index, name in enumerate(get_template_variables(old.template))
	}
	for name in get_template_variables(old.header):
		rows.setdefault(name, name)
	return [{"variable_name": name, "variable_example": example} for name, example in rows.items()]


def _copy_message(old, templates: dict) -> None:
	incoming = old.type == "Incoming"
	if incoming:
		profile = get_or_create_profile(
			f"+{old.get('from')}", old.whatsapp_account, old.profile_name, old.get("from")
		)
		sender = None
		status = "Sent"
	else:
		profile = get_or_create_profile(old.to, old.whatsapp_account)
		sender = frappe.db.get_value("WA Account", old.whatsapp_account, "phone_id")
		status = OUTGOING_STATUS.get((old.status or "").lower(), "Sent")

	is_reaction = old.content_type == "reaction"
	context_message_id = old.reply_to_message_id if (old.is_reply or is_reaction) else None

	frappe.get_doc(
		{
			"doctype": "WA Message",
			"name": old.name,
			"owner": old.owner,
			"modified_by": old.modified_by,
			"creation": old.creation,
			"modified": old.modified,
			"docstatus": 1,
			"direction": old.type,
			"to": profile,
			"from": sender,
			"whatsapp_account": old.whatsapp_account,
			"message": strip_html_tags(old.message or ""),
			"status": status,
			"message_id": old.message_id,
			"conversation_id": old.conversation_id,
			"timestamp": old.creation,
			"reference_doctype": old.reference_doctype,
			"reference_docname": old.reference_name,
			"is_template": old.use_template,
			"whatsapp_template": templates.get(old.template),
			"template_body_parameters": old.template_parameters,
			"template_header_parameters": old.template_header_parameters,
			"reaction": old.message if is_reaction else None,
			"context_message_id": context_message_id,
			"reply_to_message": _replied_message(context_message_id),
			"attach": old.attach,
			"media_url": old.attach,
			"mime_type": mimetypes.guess_type(old.attach)[0] if old.attach else None,
		}
	).db_insert()


def _replied_message(message_id: str | None) -> str | None:
	if not message_id:
		return None
	return frappe.db.get_value(OLD_MESSAGE, {"message_id": message_id}, "name")
