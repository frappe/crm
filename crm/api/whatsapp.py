import json
import re

import frappe
from frappe import _
from frappe.permissions import add_permission, update_permission_property

from crm.api.doc import get_assigned_users
from crm.fcrm.doctype.crm_notification.crm_notification import notify_user
from crm.integrations.api import get_all_matches_by_phone_number, get_contact_lead_or_deal_from_number

ALLOWED_WHATSAPP_ROLES = ["System Manager", "Sales Manager", "Sales User"]

MIME_CONTENT_TYPE_MAP = {
	"image/": "image",
	"audio/": "audio",
	"video/": "video",
}


def _get_default_whatsapp_account() -> str | None:
	"""Get the default WhatsApp account from settings."""
	if not frappe.db.exists("DocType", "Whatsapp Setting"):
		return None
	return frappe.db.get_single_value("Whatsapp Setting", "default_account")


def _resolve_to_profile(to_value: str, create_if_missing: bool = False) -> str | None:
	"""Resolve a value (phone number or profile name) to a Whatsapp Profile name.

	Accepts either:
	- A Whatsapp Profile name (returns as-is if exists)
	- A phone number (looks up by phone + default account, optionally creates)

	Returns the Profile name, or None if not found/created.
	"""
	if not to_value:
		return None

	if not frappe.db.exists("DocType", "Whatsapp Profile"):
		return None

	if frappe.db.exists("Whatsapp Profile", to_value):
		return to_value

	default_account = _get_default_whatsapp_account()
	if not default_account:
		return None

	profile_name = frappe.db.get_value(
		"Whatsapp Profile",
		{"phone_number": to_value, "whatsapp_account": default_account},
		"name",
	)
	if profile_name:
		return profile_name

	if not create_if_missing:
		return None

	try:
		from whatsapp.whatsapp.doctype.whatsapp_profile.whatsapp_profile import (
			get_or_create_profile,
		)

		return get_or_create_profile(
			phone_number=to_value,
			account_name=default_account,
			profile_name=to_value,
			wa_id=to_value,
		)
	except ImportError:
		return None
	except Exception:
		frappe.log_error(frappe.get_traceback(), "CRM WhatsApp: failed to resolve/create profile")
		return None


def _validate_template_for_reference(template_name: str, reference_doctype: str) -> None:
	"""Enforce the Whatsapp Template "reference DocType drives all parameters" invariant.

	Per the Whatsapp app's design, a template with variables resolves them from a
	single document of the template's bound reference_doctype. Sending such a
	template from a different doctype (or from no doctype) cannot resolve values.
	"""
	if not frappe.db.exists("Whatsapp Template", template_name):
		frappe.throw(
			_("WhatsApp Template '{0}' does not exist.").format(template_name),
			frappe.DoesNotExistError,
		)

	template = frappe.get_cached_doc("Whatsapp Template", template_name)
	if not template.get("template_variables"):
		return

	template_ref = template.get("reference_doctype")
	if not template_ref:
		frappe.throw(
			_(
				"Template '{0}' has unfilled variables but is not bound to a reference DocType, "
				"so variable values cannot be auto-filled."
			).format(template_name)
		)

	if template_ref != reference_doctype:
		frappe.throw(
			_("Template '{0}' resolves variables from {1}; cannot send from {2}.").format(
				template_name, template_ref, reference_doctype
			)
		)

	unmapped = [var.variable_name for var in template.get("template_variables") if not var.variable_field]
	if unmapped:
		frappe.throw(
			_(
				"Template '{0}' has variables without a mapped field: {1}. "
				"Set Variable Field on each Template Variable row before sending."
			).format(template_name, ", ".join(unmapped))
		)


def validate_access(reference_doctype=None, reference_name=None, permtype="read"):
	if not any(role in ALLOWED_WHATSAPP_ROLES for role in frappe.get_roles()):
		frappe.throw(_("Only sales users can access WhatsApp features."), frappe.PermissionError)

	if reference_doctype and reference_name:
		if not frappe.db.exists(reference_doctype, reference_name):
			frappe.throw(
				_("Reference document {0} {1} does not exist.").format(reference_doctype, reference_name),
				frappe.DoesNotExistError,
			)
		reference_doc = frappe.get_doc(reference_doctype, reference_name)
		if not reference_doc.has_permission(permtype):
			frappe.throw(
				_("Not permitted to access reference document {0} {1}.").format(
					reference_doctype, reference_name
				),
				frappe.PermissionError,
			)
		return reference_doc

	return None


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
	"""Get phone number from the Whatsapp Profile linked via doc.to (Link field)."""
	profile_name = doc.get("to")
	if not profile_name:
		return None

	try:
		if not frappe.db.exists("Whatsapp Profile", profile_name):
			return None
		return frappe.db.get_value("Whatsapp Profile", profile_name, "phone_number")
	except Exception:
		return None


def _link_profile_to_crm_entities(doc) -> None:
	"""Link Whatsapp Profile to ALL matching CRM entities (Deal, Lead, Contact).

	Uses Dynamic Link table (Whatsapp Profile.links) to link to matching CRM entities.
	Idempotent: skips if already linked.
	"""
	profile_name = doc.get("to")
	if not profile_name:
		return

	try:
		if not frappe.db.exists("Whatsapp Profile", profile_name):
			return

		phone_number = frappe.db.get_value("Whatsapp Profile", profile_name, "phone_number")
		if not phone_number:
			return

		matches = get_all_matches_by_phone_number(phone_number)
		if not matches:
			return

		profile = frappe.get_doc("Whatsapp Profile", profile_name)

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


def on_update(doc, method):
	frappe.publish_realtime(
		"whatsapp_message",
		{
			"reference_doctype": doc.reference_doctype,
			"reference_docname": doc.reference_docname,
		},
	)

	notify_agent(doc)


def notify_agent(doc):
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
					"reference_doctype": "Whatsapp Message",
					"reference_docname": doc.name,
					"redirect_to_doctype": doc.reference_doctype,
					"redirect_to_docname": doc.reference_docname,
				}
			)


@frappe.whitelist()
def is_whatsapp_enabled():
	if not frappe.db.exists("DocType", "Whatsapp Setting"):
		return False
	default_account = frappe.get_cached_value("Whatsapp Setting", "Whatsapp Setting", "default_account")
	if not default_account:
		return False
	status = frappe.get_cached_value("Whatsapp Account", default_account, "status")
	return status == "Active"


@frappe.whitelist()
def is_whatsapp_installed():
	if not frappe.db.exists("DocType", "Whatsapp Setting"):
		return False
	return True


def _infer_content_type(mime_type):
	if not mime_type:
		return "text"
	for prefix, ctype in MIME_CONTENT_TYPE_MAP.items():
		if mime_type.lower().startswith(prefix):
			return ctype
	return "document"


@frappe.whitelist()
def get_whatsapp_messages(reference_doctype: str, reference_name: str):
	reference_doc = validate_access(reference_doctype, reference_name)
	if "twilio_integration" in frappe.get_installed_apps():
		return []
	if not frappe.db.exists("DocType", "Whatsapp Message"):
		return []
	messages = []

	if reference_doctype == "CRM Deal":
		lead = reference_doc.get("lead")
		if lead:
			validate_access("CRM Lead", lead)
			messages = frappe.get_all(
				"Whatsapp Message",
				filters={
					"reference_doctype": "CRM Lead",
					"reference_docname": lead,
				},
				fields=[
					"name",
					"direction",
					"to",
					"from",
					"mime_type",
					"is_template",
					"media_url",
					"whatsapp_template",
					"message_id",
					"context_message_id",
					"creation",
					"message",
					"status",
					"reference_doctype",
					"reference_docname",
					"template_body_parameters",
					"template_header_parameters",
				],
			)

	messages += frappe.get_all(
		"Whatsapp Message",
		filters={
			"reference_doctype": reference_doctype,
			"reference_docname": reference_name,
		},
		fields=[
			"name",
			"direction",
			"to",
			"from",
			"mime_type",
			"is_template",
			"media_url",
			"whatsapp_template",
			"message_id",
			"context_message_id",
			"creation",
			"message",
			"status",
			"reference_doctype",
			"reference_docname",
			"template_body_parameters",
			"template_header_parameters",
		],
	)

	for message in messages:
		message["type"] = message.pop("direction")
		message["content_type"] = _infer_content_type(message.pop("mime_type"))
		message["message_type"] = "Template" if message.pop("is_template") else "Manual"
		message["use_template"] = message["message_type"] == "Template"
		message["template"] = message.pop("whatsapp_template")
		message["attach"] = message.pop("media_url")
		message["is_reply"] = bool(message["context_message_id"])
		message["reply_to_message_id"] = message.pop("context_message_id")
		message["reference_name"] = message.pop("reference_docname")
		message["template_parameters"] = message.pop("template_body_parameters")
		message["template_header_parameters"] = message.pop("template_header_parameters")

	template_messages = [message for message in messages if message["message_type"] == "Template"]
	for template_message in template_messages:
		if not frappe.db.exists("Whatsapp Template", template_message["template"]):
			continue
		template = frappe.get_doc("Whatsapp Template", template_message["template"])
		if template:
			template_message["template_name"] = template.template_name
			if template_message["template_parameters"]:
				parameters = json.loads(template_message["template_parameters"])
				template.message = parse_template_parameters(template.message, parameters)
			template_message["template"] = template.message
			if template_message["template_header_parameters"]:
				header_parameters = json.loads(template_message["template_header_parameters"])
				template.header_text = parse_template_parameters(template.header_text, header_parameters)
			template_message["header"] = template.header_text
			template_message["footer"] = template.footer

	for message in messages:
		from_name = get_from_name(message) if message["from"] else _("You")
		message["from_name"] = from_name

	reply_messages = [message for message in messages if message["is_reply"]]
	for reply_message in reply_messages:
		replied_message = next(
			(m for m in messages if m["message_id"] == reply_message["reply_to_message_id"]),
			None,
		)
		if replied_message:
			from_name = get_from_name(reply_message) if replied_message["from"] else _("You")
			message = replied_message["message"]
			if replied_message["message_type"] == "Template":
				message = replied_message["template"]
			reply_message["reply_message"] = message
			reply_message["header"] = replied_message.get("header") or ""
			reply_message["footer"] = replied_message.get("footer") or ""
			reply_message["reply_to"] = replied_message["name"]
			reply_message["reply_to_direction"] = replied_message["type"]
			reply_message["reply_to_from"] = from_name

	return messages


@frappe.whitelist()
def create_whatsapp_message(
	reference_doctype: str,
	reference_name: str,
	message: str,
	to: str,
	attach: str,
	reply_to: str,
	content_type: str = "text",
):
	validate_access(reference_doctype, reference_name)

	profile_name = _resolve_to_profile(to, create_if_missing=True)
	if not profile_name:
		frappe.throw(
			_(
				"Could not resolve recipient '{0}' to a WhatsApp Profile. Please ensure a default WhatsApp account is configured."
			).format(to)
		)

	doc = frappe.new_doc("Whatsapp Message")

	if reply_to:
		if not frappe.db.exists("Whatsapp Message", reply_to):
			frappe.throw(_("Referenced WhatsApp message does not exist."), frappe.DoesNotExistError)
		reply_doc = frappe.get_doc("Whatsapp Message", reply_to)
		if not reply_doc.has_permission("read"):
			frappe.throw(
				_("Not permitted to access the referenced WhatsApp message."), frappe.PermissionError
			)
		validate_access(reply_doc.reference_doctype, reply_doc.reference_docname)
		doc.update(
			{
				"context_message_id": reply_doc.message_id,
			}
		)

	doc.update(
		{
			"reference_doctype": reference_doctype,
			"reference_docname": reference_name,
			"message": message or attach,
			"to": profile_name,
		}
	)
	doc.insert(ignore_permissions=True)

	if attach:
		mime_map = {
			"image": "image/jpeg",
			"document": "application/pdf",
			"audio": "audio/mp4",
			"video": "video/mp4",
		}
		frappe.db.set_value("Whatsapp Message", doc.name, "media_url", attach, update_modified=False)
		frappe.db.set_value(
			"Whatsapp Message", doc.name, "mime_type", mime_map.get(content_type, ""), update_modified=False
		)
		doc.reload()

	try:
		doc.submit()
	except Exception:
		pass
	return doc.name


@frappe.whitelist()
def send_whatsapp_template(reference_doctype: str, reference_name: str, template: str, to: str):
	validate_access(reference_doctype, reference_name)

	_validate_template_for_reference(template, reference_doctype)

	profile_name = _resolve_to_profile(to, create_if_missing=True)
	if not profile_name:
		frappe.throw(
			_(
				"Could not resolve recipient '{0}' to a WhatsApp Profile. Please ensure a default WhatsApp account is configured."
			).format(to)
		)

	doc = frappe.new_doc("Whatsapp Message")
	doc.update(
		{
			"reference_doctype": reference_doctype,
			"reference_docname": reference_name,
			"is_template": True,
			"message": "Template message",
			"whatsapp_template": template,
			"to": profile_name,
		}
	)
	doc.insert(ignore_permissions=True)
	try:
		doc.submit()
	except Exception:
		pass
	return doc.name


@frappe.whitelist()
def react_on_whatsapp_message(emoji: str, reply_to_name: str):
	validate_access()
	if not frappe.db.exists("Whatsapp Message", reply_to_name):
		frappe.throw(_("Referenced WhatsApp message does not exist."), frappe.DoesNotExistError)
	reply_to_doc = frappe.get_doc("Whatsapp Message", reply_to_name)

	if not reply_to_doc.has_permission("read"):
		frappe.throw(_("Not permitted to access the referenced WhatsApp message."), frappe.PermissionError)

	validate_access(reply_to_doc.reference_doctype, reply_to_doc.reference_docname)

	to = reply_to_doc.to
	doc = frappe.new_doc("Whatsapp Message")
	doc.update(
		{
			"reference_doctype": reply_to_doc.reference_doctype,
			"reference_docname": reply_to_doc.reference_docname,
			"message": emoji,
			"to": to,
			"context_message_id": reply_to_doc.message_id,
		}
	)
	doc.insert(ignore_permissions=True)
	try:
		doc.submit()
	except Exception:
		pass
	return doc.name


_PLACEHOLDER_RE = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")


def parse_template_parameters(string, parameters):
	"""Substitute `{{var}}` placeholders in `string` using `parameters`.

	The upstream Whatsapp app stores parameters in three shapes:
	- dict: named templates (the authoring default) and synced positional
	  templates with numeric-string keys → substitute `{{<key>}}` per entry
	- list: legacy positional shape → substitute `{{1}}`, `{{2}}`, … by index
	- scalar (str/int/float): header storage, which keeps only the single
	  value (Meta's header section takes one variable) → substitute the
	  first placeholder in `string`
	"""
	if not string or parameters is None:
		return string

	if isinstance(parameters, dict):
		return _PLACEHOLDER_RE.sub(
			lambda m: str(parameters[m.group(1)]) if m.group(1) in parameters else m.group(0),
			string,
		)

	if isinstance(parameters, list):

		def _replace_positional(match):
			key = match.group(1)
			if key.isdigit():
				index = int(key) - 1
				if 0 <= index < len(parameters):
					return str(parameters[index])
			return match.group(0)

		return _PLACEHOLDER_RE.sub(_replace_positional, string)

	return _PLACEHOLDER_RE.sub(lambda _m: str(parameters), string, count=1)


def get_from_name(message):
	doc = frappe.get_doc(message["reference_doctype"], message["reference_name"])
	from_name = ""
	if message["reference_doctype"] == "CRM Deal":
		if doc.get("contacts"):
			for c in doc.get("contacts"):
				if c.is_primary:
					from_name = c.full_name or c.mobile_no
					break
		else:
			from_name = doc.get("lead_name")
	else:
		from_name = " ".join(name for name in [doc.get("first_name"), doc.get("last_name")] if name)
	return from_name


@frappe.whitelist()
def get_sendable_templates(reference_doctype: str) -> list[dict]:
	"""Return APPROVED templates that can be sent from the given CRM doctype.

	A template is sendable from `reference_doctype` when either:
	- it is bound to that doctype (variables resolve from the open document), or
	- it is unbound AND has no variables (nothing to resolve).

	Unbound templates with variables are excluded because their variables
	cannot be auto-filled (see Whatsapp app DESIGN_DECISIONS.md).
	"""
	validate_access()

	if not frappe.db.exists("DocType", "Whatsapp Template"):
		return []

	templates = frappe.get_all(
		"Whatsapp Template",
		filters={
			"status": "APPROVED",
			"reference_doctype": ["in", [reference_doctype, ""]],
		},
		fields=["name", "message", "footer", "header_text", "header_type", "reference_doctype"],
		order_by="modified desc",
	)

	if not templates:
		return []

	unbound_names = [t.name for t in templates if not t.reference_doctype]
	unbound_with_vars: set[str] = set()
	if unbound_names:
		unbound_with_vars = {
			row.parent
			for row in frappe.get_all(
				"Template Variable",
				filters={"parent": ["in", unbound_names], "parenttype": "Whatsapp Template"},
				fields=["parent"],
			)
		}

	return [t for t in templates if t.name not in unbound_with_vars]


@frappe.whitelist()
def get_linked_whatsapp_profiles(reference_doctype: str, reference_docname: str) -> list[dict]:
	"""Get all Whatsapp Profiles linked to the given CRM document.

	Searches Dynamic Link table where:
	- parenttype = "Whatsapp Profile"
	- link_doctype = reference_doctype
	- link_name = reference_docname

	Returns list of profile details: name, profile_name, phone_number, status, wa_id,
	last_message_at, message_count.
	"""
	validate_access(reference_doctype, reference_docname)

	if not frappe.db.exists("DocType", "Whatsapp Profile"):
		return []

	links = frappe.get_all(
		"Dynamic Link",
		filters={
			"parenttype": "Whatsapp Profile",
			"link_doctype": reference_doctype,
			"link_name": reference_docname,
		},
		fields=["parent as profile_name"],
	)

	if not links:
		return []

	profiles = frappe.get_all(
		"Whatsapp Profile",
		filters={"name": ["in", [l.profile_name for l in links]]},
		fields=[
			"name",
			"profile_name",
			"phone_number",
			"status",
			"wa_id",
			"last_message_at",
			"message_count",
		],
	)

	return profiles


def add_roles():
	if "whatsapp" not in frappe.get_installed_apps():
		return

	role_list = ["Sales Manager", "Sales User"]
	doctypes = [
		"Whatsapp Message",
		"Whatsapp Template",
		"Whatsapp Setting",
		"Whatsapp Profile",
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
