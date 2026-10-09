import frappe
from frappe import _
from frappe.permissions import add_permission, update_permission_property
from frappe.query_builder.functions import Count
from pypika import Criterion

from crm.api.doc import get_assignees
from crm.fcrm.doctype.crm_notification.crm_notification import notify_user
from crm.integrations.api import find_by_phone, get_contact_lead_or_deal_from_number
from crm.utils import normalize_phone

ALLOWED_WHATSAPP_ROLES = ["System Manager", "Sales Manager", "Sales User"]
LEAD_SOURCE = "WhatsApp"
CONFIRM_PARAM = "confirm_whatsapp_recipient_change"


class WhatsAppRecipientChangeError(frappe.ValidationError):
	pass


def validate_access() -> None:
	"""Registered as the WhatsApp app's `whatsapp_access_guard` hook, which calls it before
	every client-facing endpoint. The app permission-checks the reference document itself;
	this is CRM's orthogonal role policy on top."""
	if not any(role in ALLOWED_WHATSAPP_ROLES for role in frappe.get_roles()):
		frappe.throw(_("Only sales users can access WhatsApp features."), frappe.PermissionError)


def validate(doc, method):
	# preserve the user's chosen reference for outgoing messages
	if doc.direction == "Outgoing" and doc.reference_doctype and doc.reference_docname:
		pass
	else:
		phone_number = _get_phone_number_from_profile(doc)
		if phone_number:
			_resolve_reference(doc, phone_number)

	_link_profile_to_crm_entities(doc)


def _resolve_reference(doc, phone_number: str) -> None:
	try:
		name, doctype = get_contact_lead_or_deal_from_number(phone_number)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "CRM WhatsApp: failed to resolve contact from number")
		return

	if not name and doc.direction == "Incoming":
		action = _lead_append_action(doc.whatsapp_account)
		if action:
			name, doctype = _create_lead(doc, action), "CRM Lead"

	if name:
		doc.reference_doctype = doctype
		doc.reference_docname = name


def _lead_append_action(account: str | None):
	"""An account that appends incoming messages to CRM Lead has asked for leads from new
	senders; that configuration is the opt-in, there is no separate switch."""
	if not account:
		return None
	for action in frappe.get_cached_doc("WA Account", account).get("append_actions", []):
		if action.append_to == "CRM Lead" and action.trigger_on in ("Incoming", "Both"):
			return action
	return None


def _create_lead(doc, action) -> str:
	"""Built as the whatsapp app's append action would build it, so the message's reference
	is set before that action runs and it finds nothing left to do. The source is the one
	thing the whatsapp app cannot know."""
	profile = frappe.get_cached_doc("WA Profile", doc.to)
	lead = frappe.new_doc("CRM Lead")
	lead.set(action.sender_field, profile.phone_number)
	lead.set(action.sender_name_field, profile.profile_name)
	if action.message_field:
		lead.set(action.message_field, doc.message)
	if action.timestamp_field:
		lead.set(action.timestamp_field, doc.timestamp)
	if frappe.db.exists("CRM Lead Source", LEAD_SOURCE):
		lead.source = LEAD_SOURCE
	lead.insert(ignore_permissions=True)
	return lead.name


def _get_phone_number_from_profile(doc) -> str | None:
	"""Get phone number from the WhatsApp Profile linked via doc.to (Link field)."""
	profile_name = doc.get("to")
	if not profile_name:
		return None

	try:
		if not frappe.db.exists("WA Profile", profile_name):
			return None
		return frappe.db.get_value("WA Profile", profile_name, "phone_number")
	except Exception:
		return None


def _link_profile_to_crm_entities(doc) -> None:
	"""Link WhatsApp Profile to ALL matching CRM entities (Deal, Lead, Contact).

	Uses Dynamic Link table (WA Profile.links) to link to matching CRM entities.
	Idempotent: skips if already linked.
	"""
	profile_name = doc.get("to")
	if not profile_name:
		return

	try:
		if not frappe.db.exists("WA Profile", profile_name):
			return

		phone_number = frappe.db.get_value("WA Profile", profile_name, "phone_number")
		if not phone_number:
			return

		matches = find_by_phone(phone_number)
		if not matches:
			return

		profile = frappe.get_doc("WA Profile", profile_name)

		existing_links = {(link.link_doctype, link.link_name) for link in (profile.links or [])}

		needs_save = False
		for match in matches:
			doctype = match["doctype"]
			docname = match["docname"]
			key = (doctype, docname)

			if key not in existing_links:
				profile.append(
					"links",
					{
						"link_doctype": doctype,
						"link_name": docname,
						"link_title": docname,
					},
				)
				needs_save = True

		if needs_save:
			profile.flags.ignore_permissions = True
			profile.save(ignore_permissions=True)

	except Exception:
		frappe.log_error(frappe.get_traceback(), "CRM WhatsApp: failed to link profile to CRM entities")


def notify_agent(doc, method=None):
	if doc.direction == "Incoming":
		if not doc.reference_doctype or not doc.reference_docname:
			return
		doctype = doc.reference_doctype
		if doctype and doctype.startswith("CRM "):
			doctype = doctype[4:].lower()
		safe_reference_docname = frappe.utils.escape_html(doc.reference_docname)
		notification_text = f"""
            <div class="mb-2 leading-5 text-ink-gray-5">
                <span class="font-medium text-ink-gray-9">{_("You")}</span>
                <span>{_("received a whatsapp message in {0}").format(doctype)}</span>
                <span class="font-medium text-ink-gray-9">{safe_reference_docname}</span>
            </div>
        """
		assigned_users = get_assignees(doc.reference_doctype, doc.reference_docname)
		for user in assigned_users:
			notify_user(
				{
					"owner": doc.owner,
					"assigned_to": user,
					"notification_type": "WhatsApp",
					"message": doc.message,
					"notification_text": notification_text,
					"reference_doctype": "WA Message",
					"reference_docname": doc.name,
					"redirect_to_doctype": doc.reference_doctype,
					"redirect_to_docname": doc.reference_docname,
				}
			)


def guard_doc_recipient_change(doc) -> None:
	"""`guard_recipient_change` for a Lead or Deal being saved."""
	before = doc.get_doc_before_save()
	if doc.is_new() or not before:
		return
	guard_recipient_change(doc.doctype, doc.name, before.mobile_no, doc.mobile_no)


def guard_recipient_change(
	doctype: str, docname: str, old_number: str | None, new_number: str | None
) -> None:
	"""Refuse to move a Lead or Deal off a number it has a WhatsApp conversation with,
	unless the request carries the user's confirmation. Replies from the old number stop
	showing on the record after the change, so the user has to know before it happens."""
	if not old_number or normalize_phone(old_number) == normalize_phone(new_number):
		return
	if frappe.form_dict.get(CONFIRM_PARAM) or _is_unattended():
		return

	count = count_conversation(doctype, docname, old_number)
	if not count:
		return

	record = _("deal") if doctype == "CRM Deal" else _("lead")
	if new_number:
		outcome = _("New messages will go to {0}.").format(new_number)
	else:
		outcome = _("You won't be able to message them from this {0}.").format(record)

	frappe.throw(
		_(
			"This {0} has {1} WhatsApp message(s) with {2}. After this change, their replies won't show here. {3}"
		).format(record, count, old_number, outcome),
		WhatsAppRecipientChangeError,
		title=_("Change WhatsApp recipient?"),
	)


def count_conversation(doctype: str, docname: str, phone_number: str) -> int:
	"""Messages the WhatsApp tab of this record shows for the given number: a Deal also
	shows the messages of the Lead it was converted from."""
	target = normalize_phone(phone_number)
	if not target:
		return 0

	references = [(doctype, docname)]
	if doctype == "CRM Deal" and (lead := frappe.db.get_value("CRM Deal", docname, "lead")):
		references.append(("CRM Lead", lead))

	Message = frappe.qb.DocType("WA Message")
	Profile = frappe.qb.DocType("WA Profile")
	rows = (
		frappe.qb.from_(Message)
		.join(Profile)
		.on(Message.to == Profile.name)
		.select(Profile.phone_number, Count("*"))
		.where(
			Criterion.any(
				(Message.reference_doctype == ref_doctype) & (Message.reference_docname == ref_docname)
				for ref_doctype, ref_docname in references
			)
		)
		.groupby(Profile.phone_number)
	).run()

	return sum(count for phone, count in rows if normalize_phone(phone) == target)


def _is_unattended() -> bool:
	"""No one is there to confirm: data import, patches, install and migrate."""
	flags = frappe.flags
	return bool(flags.in_import or flags.in_patch or flags.in_install or flags.in_migrate)


@frappe.whitelist()
def is_whatsapp_enabled():
	if not frappe.db.exists("DocType", "WA Settings"):
		return False
	default_account = frappe.get_cached_value("WA Settings", "WA Settings", "default_account")
	if not default_account:
		return False
	status = frappe.get_cached_value("WA Account", default_account, "status")
	return status == "Active"


# Link fields pointing at WA Account. Frappe refuses to delete a document that
# any of these still reference, so these counts are what makes a delete impossible.
ACCOUNT_LINK_FIELDS = {
	"WA Message": "whatsapp_account",
	"WA Profile": "whatsapp_account",
	"WA Template": "whatsapp_account",
	"WA Log": "account",
}


@frappe.whitelist()
def get_account_usage(account: str) -> dict[str, int]:
	"""Count what an account is still referenced by, so the UI can explain a refused
	delete up front instead of surfacing Frappe's link-exists error."""
	validate_access()

	usage = {}
	for doctype, fieldname in ACCOUNT_LINK_FIELDS.items():
		if not frappe.db.exists("DocType", doctype):
			continue
		usage[doctype] = frappe.db.count(doctype, {fieldname: account})

	return usage


@frappe.whitelist()
def is_whatsapp_installed():
	if not frappe.db.exists("DocType", "WA Settings"):
		return False
	return True


def add_roles():
	if "whatsapp" not in frappe.get_installed_apps():
		return

	role_list = ["Sales Manager", "Sales User"]
	doctypes = [
		"WA Message",
		"WA Template",
		"WA Settings",
		"WA Profile",
	]
	for doctype in doctypes:
		for role in role_list:
			if frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role}):
				continue
			add_permission(doctype, role, 0, "write")
			update_permission_property(doctype, role, 0, "create", 1)
			update_permission_property(doctype, role, 0, "delete", 1)
			update_permission_property(doctype, role, 0, "share", 1)
			update_permission_property(doctype, role, 0, "email", 1)
			update_permission_property(doctype, role, 0, "print", 1)
			update_permission_property(doctype, role, 0, "report", 1)
			update_permission_property(doctype, role, 0, "export", 1)
