import functools

import frappe
import phonenumbers
import requests
from frappe import _
from frappe.model.docstatus import DocStatus
from frappe.model.dynamic_links import get_dynamic_link_map
from frappe.utils import floor
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


# Extracted from frappe core frappe/model/delete_doc.py/check_if_doc_is_linked
def get_linked_docs(doc, method="Delete"):
	from frappe.model.rename_doc import get_link_fields

	link_fields = get_link_fields(doc.doctype)
	ignored_doctypes = set()

	if method == "Cancel" and (doc_ignore_flags := doc.get("ignore_linked_doctypes")):
		ignored_doctypes.update(doc_ignore_flags)
	if method == "Delete":
		ignored_doctypes.update(frappe.get_hooks("ignore_links_on_delete"))

	docs = []

	for lf in link_fields:
		link_dt, link_field, issingle = lf["parent"], lf["fieldname"], lf["issingle"]
		if link_dt in ignored_doctypes or (link_field == "amended_from" and method == "Cancel"):
			continue

		try:
			meta = frappe.get_meta(link_dt)
		except frappe.DoesNotExistError:
			frappe.clear_last_message()
			# This mostly happens when app do not remove their customizations, we shouldn't
			# prevent link checks from failing in those cases
			continue

		if issingle:
			if frappe.db.get_single_value(link_dt, link_field) == doc.name:
				docs.append({"doc": doc.name, "link_dt": link_dt, "link_field": link_field})
			continue

		fields = ["name", "docstatus"]

		if meta.istable:
			fields.extend(["parent", "parenttype"])

		for item in frappe.db.get_values(link_dt, {link_field: doc.name}, fields, as_dict=True):
			# available only in child table cases
			item_parent = getattr(item, "parent", None)
			linked_parent_doctype = item.parenttype if item_parent else link_dt

			if linked_parent_doctype in ignored_doctypes:
				continue

			if method != "Delete" and (method != "Cancel" or not DocStatus(item.docstatus).is_submitted()):
				# don't raise exception if not
				# linked to a non-cancelled doc when deleting or to a submitted doc when cancelling
				continue
			elif link_dt == doc.doctype and (item_parent or item.name) == doc.name:
				# don't raise exception if not
				# linked to same item or doc having same name as the item
				continue
			else:
				reference_docname = item_parent or item.name
				docs.append(
					{
						"doc": doc.name,
						"reference_doctype": linked_parent_doctype,
						"reference_docname": reference_docname,
					}
				)
	return docs


# Extracted from frappe core frappe/model/delete_doc.py/check_if_doc_is_dynamically_linked
def get_dynamic_linked_docs(doc, method="Delete"):
	docs = []
	for df in get_dynamic_link_map().get(doc.doctype, []):
		ignore_linked_doctypes = doc.get("ignore_linked_doctypes") or []

		if df.parent in frappe.get_hooks("ignore_links_on_delete") or (
			df.parent in ignore_linked_doctypes and method == "Cancel"
		):
			# don't check for communication and todo!
			continue

		meta = frappe.get_meta(df.parent)
		if meta.issingle:
			# dynamic link in single doc
			refdoc = frappe.db.get_singles_dict(df.parent)
			if (
				refdoc.get(df.options) == doc.doctype
				and refdoc.get(df.fieldname) == doc.name
				and (
					# linked to an non-cancelled doc when deleting
					(method == "Delete" and not DocStatus(refdoc.docstatus).is_cancelled())
					# linked to a submitted doc when cancelling
					or (method == "Cancel" and DocStatus(refdoc.docstatus).is_submitted())
				)
			):
				docs.append({"doc": doc.name, "reference_doctype": df.parent, "reference_docname": df.parent})
		else:
			# dynamic link in table
			df["table"] = ", `parent`, `parenttype`, `idx`" if meta.istable else ""
			for refdoc in frappe.db.sql(
				"""select `name`, `docstatus` {table} from `tab{parent}` where
				`{options}`=%s and `{fieldname}`=%s""".format(**df),
				(doc.doctype, doc.name),
				as_dict=True,
			):
				# linked to an non-cancelled doc when deleting
				# or linked to a submitted doc when cancelling
				if (method == "Delete" and not DocStatus(refdoc.docstatus).is_cancelled()) or (
					method == "Cancel" and DocStatus(refdoc.docstatus).is_submitted()
				):
					reference_doctype = refdoc.parenttype if meta.istable else df.parent
					reference_docname = refdoc.parent if meta.istable else refdoc.name

					if reference_doctype in frappe.get_hooks("ignore_links_on_delete") or (
						reference_doctype in ignore_linked_doctypes and method == "Cancel"
					):
						# don't check for communication and todo!
						continue

					at_position = f"at Row: {refdoc.idx}" if meta.istable else ""

					docs.append(
						{
							"doc": doc.name,
							"reference_doctype": reference_doctype,
							"reference_docname": reference_docname,
							"at_position": at_position,
						}
					)
	return docs


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

def is_version_16():
    from frappe.pulse.utils import get_frappe_version

    version = get_frappe_version()
    return version.startswith("16.")