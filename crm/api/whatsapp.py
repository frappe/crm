import frappe
from frappe import _
from frappe.permissions import add_permission, update_permission_property
from frappe.query_builder import Order
from pypika.functions import Replace

from crm.api.doc import get_assigned_users
from crm.fcrm.doctype.crm_notification.crm_notification import notify_user
from crm.integrations.api import get_contact_lead_or_deal_from_number
from crm.utils import are_same_phone_number, parse_phone_number

ALLOWED_WHATSAPP_ROLES = ["System Manager", "Sales Manager", "Sales User"]


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
			try:
				name, doctype = get_contact_lead_or_deal_from_number(phone_number)
				if doctype and name is not None:
					doc.reference_doctype = doctype
					doc.reference_docname = name
			except Exception:
				frappe.log_error(
					frappe.get_traceback(), "CRM WhatsApp: failed to resolve contact from number"
				)

	_link_profile_to_crm_entities(doc)


def _get_phone_number_from_profile(doc) -> str | None:
	"""Get phone number from the WhatsApp Profile linked via doc.to (Link field)."""
	profile_name = doc.get("to")
	if not profile_name:
		return None

	try:
		if not frappe.db.exists("WhatsApp Profile", profile_name):
			return None
		return frappe.db.get_value("WhatsApp Profile", profile_name, "phone_number")
	except Exception:
		return None


def _link_profile_to_crm_entities(doc) -> None:
	"""Link WhatsApp Profile to ALL matching CRM entities (Deal, Lead, Contact).

	Uses Dynamic Link table (WhatsApp Profile.links) to link to matching CRM entities.
	Idempotent: skips if already linked.
	"""
	profile_name = doc.get("to")
	if not profile_name:
		return

	try:
		if not frappe.db.exists("WhatsApp Profile", profile_name):
			return

		phone_number = frappe.db.get_value("WhatsApp Profile", profile_name, "phone_number")
		if not phone_number:
			return

		matches = get_all_matches_by_phone_number(phone_number)
		if not matches:
			return

		profile = frappe.get_doc("WhatsApp Profile", profile_name)

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
		assigned_users = get_assigned_users(doc.reference_doctype, doc.reference_docname)
		for user in assigned_users:
			notify_user(
				{
					"owner": doc.owner,
					"assigned_to": user,
					"notification_type": "WhatsApp",
					"message": doc.message,
					"notification_text": notification_text,
					"reference_doctype": "WhatsApp Message",
					"reference_docname": doc.name,
					"redirect_to_doctype": doc.reference_doctype,
					"redirect_to_docname": doc.reference_docname,
				}
			)


@frappe.whitelist()
def is_whatsapp_enabled():
	# twilio_integration declares its own DocType named "WhatsApp Message", with an unrelated
	# schema (sent_received/from_/media_link). Only one can own the name, so with it installed
	# the whatsapp app's fields may not exist on the table this tab would query.
	if "twilio_integration" in frappe.get_installed_apps():
		return False
	if not frappe.db.exists("DocType", "WhatsApp Settings"):
		return False
	default_account = frappe.get_cached_value("WhatsApp Settings", "WhatsApp Settings", "default_account")
	if not default_account:
		return False
	status = frappe.get_cached_value("WhatsApp Account", default_account, "status")
	return status == "Active"


# Link fields pointing at WhatsApp Account. Frappe refuses to delete a document that
# any of these still reference, so these counts are what makes a delete impossible.
ACCOUNT_LINK_FIELDS = {
	"WhatsApp Message": "whatsapp_account",
	"WhatsApp Profile": "whatsapp_account",
	"WhatsApp Template": "whatsapp_account",
	"WhatsApp Log": "account",
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
	if not frappe.db.exists("DocType", "WhatsApp Settings"):
		return False
	return True


def add_roles():
	if "whatsapp" not in frappe.get_installed_apps():
		return

	role_list = ["Sales Manager", "Sales User"]
	doctypes = [
		"WhatsApp Message",
		"WhatsApp Template",
		"WhatsApp Settings",
		"WhatsApp Profile",
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


# TODO: duplicates the phone matching in crm.integrations.api.get_contact(), unify later
def get_all_matches_by_phone_number(phone_number: str) -> list[dict]:
	"""Get ALL matching CRM entities (Contact, Deal, Lead) for a phone number.

	Unlike get_contact_lead_or_deal_from_number() which returns only the
	highest-priority match, this returns ALL matching entities.

	Deliberately not whitelisted: the results are not permission-filtered, and both
	callers are server-side (profile linking above, and the patch that backfills it)
	which must see every match regardless of who triggered the save. Exposing this
	over HTTP would let any user probe a phone number and learn the names of records
	they cannot read.

	Returns list of dicts with:
	- doctype: "CRM Deal", "CRM Lead", or "Contact"
	- docname: name of the document
	- matching_phone: the phone number that matched
	"""
	number = parse_phone_number(phone_number)

	if number.get("is_valid"):
		return _get_all_matches(number.get("national_number"), number.get("country"))
	else:
		return _get_all_matches(phone_number, number.get("country"), exact_match=True)


def _get_all_matches(phone_number: str, country: str = "IN", exact_match: bool = False) -> list[dict]:
	"""Internal: find ALL matching entities by phone number."""
	if not phone_number:
		return []

	# TODO: this should be a util, this api doesn't need to handle this
	cleaned_number = (
		phone_number.strip()
		.replace(" ", "")
		.replace("-", "")
		.replace("(", "")
		.replace(")", "")
		.replace("+", "")
	)

	results = []
	seen = set()

	def _add_match(doctype: str, docname: str, matching_phone: str):
		key = (doctype, docname)
		if key not in seen:
			seen.add(key)
			results.append({"doctype": doctype, "docname": docname, "matching_phone": matching_phone})

	Contact = frappe.qb.DocType("Contact")
	normalized_phone = Replace(
		Replace(Replace(Replace(Replace(Contact.mobile_no, " ", ""), "-", ""), "(", ""), ")", ""), "+", ""
	)

	query = (
		frappe.qb.from_(Contact)
		.select(Contact.name, Contact.full_name, Contact.mobile_no, Contact.phone)
		.where(normalized_phone.like(f"%{cleaned_number}%"))
		.orderby("modified", order=Order.desc)
	)
	contacts = query.run(as_dict=True)

	for contact in contacts:
		if are_same_phone_number(contact.mobile_no, phone_number, country, validate=not exact_match):
			_add_match("Contact", contact.name, contact.mobile_no)

			deal = frappe.db.get_value("CRM Contacts", {"contact": contact.name, "is_primary": 1}, "parent")
			if deal:
				_add_match("CRM Deal", deal, contact.mobile_no)

	Lead = frappe.qb.DocType("CRM Lead")
	normalized_phone = Replace(
		Replace(Replace(Replace(Replace(Lead.mobile_no, " ", ""), "-", ""), "(", ""), ")", ""), "+", ""
	)

	query = (
		frappe.qb.from_(Lead)
		.select(Lead.name, Lead.lead_name, Lead.mobile_no, Lead.phone)
		.where(Lead.converted == 0)
		.where(normalized_phone.like(f"%{cleaned_number}%"))
		.orderby("modified", order=Order.desc)
	)
	leads = query.run(as_dict=True)

	for lead in leads:
		if are_same_phone_number(lead.mobile_no, phone_number, country, validate=not exact_match):
			_add_match("CRM Lead", lead.name, lead.mobile_no)

	return results
