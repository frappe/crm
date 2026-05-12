import functools

import frappe
import phonenumbers
from frappe import _
from frappe.core.doctype.comment.comment import Comment
from frappe.core.doctype.communication.communication import Communication
from frappe.utils import floor, now
from phonenumbers import NumberParseException
from phonenumbers import PhoneNumberFormat as PNF


def parse_phone_number(phone_number, default_country="IN"):
	try:
		# Parse the number
		number = phonenumbers.parse(phone_number, default_country)

		# Get various information about the number
		result = {
			"is_valid": phonenumbers.is_valid_number(number),
			"country_code": number.country_code,
			"national_number": str(number.national_number),
			"formats": {
				"international": phonenumbers.format_number(number, PNF.INTERNATIONAL),
				"national": phonenumbers.format_number(number, PNF.NATIONAL),
				"E164": phonenumbers.format_number(number, PNF.E164),
				"RFC3966": phonenumbers.format_number(number, PNF.RFC3966),
			},
			"type": phonenumbers.number_type(number),
			"country": phonenumbers.region_code_for_number(number),
			"is_possible": phonenumbers.is_possible_number(number),
		}

		return {"success": True, **result}
	except NumberParseException as e:
		return {"success": False, "error": str(e)}


def are_same_phone_number(number1, number2, default_region="IN", validate=True):
	"""
	Check if two phone numbers are the same, regardless of their format.

	Args:
	    number1 (str): First phone number
	    number2 (str): Second phone number
	    default_region (str): Default region code for parsing ambiguous numbers

	Returns:
	    bool: True if numbers are same, False otherwise
	"""
	try:
		# Parse both numbers
		parsed1 = phonenumbers.parse(number1, default_region)
		parsed2 = phonenumbers.parse(number2, default_region)

		# Check if both numbers are valid
		if validate and not (phonenumbers.is_valid_number(parsed1) and phonenumbers.is_valid_number(parsed2)):
			return False

		# Convert both to E164 format and compare
		formatted1 = phonenumbers.format_number(parsed1, phonenumbers.PhoneNumberFormat.E164)
		formatted2 = phonenumbers.format_number(parsed2, phonenumbers.PhoneNumberFormat.E164)

		return formatted1 == formatted2

	except phonenumbers.NumberParseException:
		return False


def seconds_to_duration(seconds):
	if not seconds:
		return "0s"

	hours = floor(seconds // 3600)
	minutes = floor((seconds % 3600) // 60)
	seconds = floor((seconds % 3600) % 60)

	# 1h 0m 0s -> 1h
	# 0h 1m 0s -> 1m
	# 0h 0m 1s -> 1s
	# 1h 1m 0s -> 1h 1m
	# 1h 0m 1s -> 1h 1s
	# 0h 1m 1s -> 1m 1s
	# 1h 1m 1s -> 1h 1m 1s

	if hours and minutes and seconds:
		return f"{hours}h {minutes}m {seconds}s"
	elif hours and minutes:
		return f"{hours}h {minutes}m"
	elif hours and seconds:
		return f"{hours}h {seconds}s"
	elif minutes and seconds:
		return f"{minutes}m {seconds}s"
	elif hours:
		return f"{hours}h"
	elif minutes:
		return f"{minutes}m"
	elif seconds:
		return f"{seconds}s"
	else:
		return "0s"


def is_admin(user: str | None = None) -> bool:
	"""
	Check whether `user` is an admin

	:param user: User to check against, defaults to current user
	:return: Whether `user` is an admin
	"""
	user = user or frappe.session.user
	return user == "Administrator"


def is_sales_user(user: str | None = None) -> bool:
	"""
	Check whether `user` is an agent

	:param user: User to check against, defaults to current user
	:return: Whether `user` is an agent
	"""
	user = user or frappe.session.user
	return is_admin() or "Sales Manager" in frappe.get_roles(user) or "Sales User" in frappe.get_roles(user)


def sales_user_only(fn):
	"""Decorator to validate if user is an agent."""

	@functools.wraps(fn)
	def wrapper(*args, **kwargs):
		if not is_sales_user():
			frappe.throw(
				msg=_("You are not permitted to access this resource."),
				title=_("Not Allowed"),
				exc=frappe.PermissionError,
			)

		return fn(*args, **kwargs)

	return wrapper


def is_frappe_version(version: str, above: bool = False, below: bool = False):
	from frappe.pulse.utils import get_frappe_version

	current_version = get_frappe_version()
	major_version = int(current_version.split(".")[0])
	target_version = int(version.split(".")[0])

	if above:
		return major_version >= target_version
	if below:
		return major_version < target_version
	return major_version == target_version


def _should_update_modified(doc: Communication | Comment) -> bool:
	if not frappe.db.get_single_value("FCRM Settings", "update_timestamp_on_new_communication"):
		return False

	if not (doc.reference_doctype and doc.reference_name):
		return False

	if doc.reference_doctype not in ["CRM Lead", "CRM Deal"]:
		return False

	if doc.doctype not in ["Comment", "Communication"]:
		return False

	return True


def _get_communication_status(doc: Communication) -> str | None:
	if doc.doctype != "Communication":
		return None

	if not (doc.reference_doctype and doc.reference_name):
		return None

	if doc.sent_or_received not in ("Sent", "Received"):
		return None

	auto_reopen = frappe.db.get_single_value("FCRM Settings", "auto_reopen_on_new_communication")
	auto_replied = frappe.db.get_single_value("FCRM Settings", "auto_mark_replied_on_response")

	if doc.sent_or_received == "Received" and auto_reopen:
		return "Open"
	elif doc.sent_or_received == "Sent" and auto_replied:
		return "Replied"

	return None


def create_lead_from_incoming_email(doc: Communication, method: str | None = None):
	if doc.doctype != "Communication":
		return

	if doc.sent_or_received != "Received" and doc.communication_type != "Communication":
		return

	if doc.reference_doctype and doc.reference_name:
		return

	if not doc.email_account:
		return

	create_lead_enabled = frappe.db.get_value(
		"Email Account", doc.email_account, "create_lead_from_incoming_email"
	)
	if not create_lead_enabled:
		return

	if frappe.db.exists("CRM Lead", {"email": doc.sender}):
		return

	lead = frappe.new_doc("CRM Lead")
	lead.email = doc.sender

	if doc.sender_full_name:
		lead.first_name = doc.sender_full_name.split(" ")[0]
		lead.last_name = (
			doc.sender_full_name.split(" ")[-1] if len(doc.sender_full_name.split(" ")) > 1 else ""
		)
	else:
		lead.first_name = doc.sender.split("@")[0]

	if frappe.db.exists("CRM Lead Source", "Email"):
		lead.source = "Email"

	lead.insert(ignore_permissions=True)

	doc.reference_doctype = "CRM Lead"
	doc.reference_name = lead.name
	doc.save(ignore_permissions=True)


def on_comment_insert(doc: Comment, method: str | None = None):
	if not (doc.reference_doctype and doc.reference_name):
		return

	if doc.reference_doctype not in ["CRM Lead", "CRM Deal"] or doc.comment_type != "Comment":
		return

	if not _should_update_modified(doc):
		return

	if doc.reference_doctype and doc.reference_name:
		frappe.enqueue(update_modified_background, doctype=doc.reference_doctype, docname=doc.reference_name)


def update_modified_background(doctype, docname):
	frappe.db.set_value(doctype, docname, "modified", now(), update_modified=False)


def on_communication_insert(doc: Communication, method: str | None = None):
	create_lead_from_incoming_email(doc)


def on_communication_update(doc: Communication, method: str | None = None):
	if not (doc.reference_doctype and doc.reference_name):
		return

	if doc.reference_doctype not in ["CRM Lead", "CRM Deal"]:
		return

	should_update_modified = _should_update_modified(doc)
	status = _get_communication_status(doc)

	values = {}

	if should_update_modified:
		values["modified"] = now()

	if status:
		last_communication = frappe.get_last_doc(
			"Communication",
			{"reference_doctype": doc.reference_doctype, "reference_name": doc.reference_name},
		)
		if last_communication and last_communication.name == doc.name:
			values["communication_status"] = status

	if not values:
		return

	frappe.db.set_value(
		doc.reference_doctype,
		doc.reference_name,
		values,
		update_modified=False,
	)
