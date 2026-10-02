import frappe
from frappe import _

from crm.api.whatsapp import guard_recipient_change


def validate(doc, method):
	update_deals_email_mobile_no(doc)


def update_deals_email_mobile_no(doc):
	linked_deals = frappe.get_all(
		"CRM Contacts",
		filters={"contact": doc.name, "is_primary": 1},
		fields=["parent"],
	)

	for linked_deal in linked_deals:
		deal = frappe.db.get_values("CRM Deal", linked_deal.parent, ["email", "mobile_no"], as_dict=True)[0]
		changed = [
			[fieldname, deal[fieldname], value]
			for fieldname, value in (("email", doc.email_id), ("mobile_no", doc.mobile_no))
			if (deal[fieldname] or "") != (value or "")
		]
		if not changed:
			continue

		guard_recipient_change("CRM Deal", linked_deal.parent, deal.mobile_no, doc.mobile_no)
		frappe.db.set_value(
			"CRM Deal", linked_deal.parent, {fieldname: new for fieldname, _old, new in changed}
		)
		add_deal_version(linked_deal.parent, changed)


def add_deal_version(deal: str, changed: list) -> None:
	"""Write the timeline entry that `frappe.db.set_value` skips but a save would have made."""
	frappe.get_doc(
		{
			"doctype": "Version",
			"ref_doctype": "CRM Deal",
			"docname": deal,
			"data": frappe.as_json({"changed": changed}),
		}
	).insert(ignore_permissions=True)


@frappe.whitelist()
def get_linked_deals(contact: str):
	"""Get linked deals for a contact"""

	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	deal_names = frappe.get_all(
		"CRM Contacts",
		filters={"contact": contact, "parenttype": "CRM Deal"},
		fields=["parent"],
		distinct=True,
	)

	# get deals data
	deals = []
	for d in deal_names:
		deal = frappe.get_cached_doc(
			"CRM Deal",
			d.parent,
			fields=[
				"name",
				"organization",
				"currency",
				"deal_value",
				"status",
				"email",
				"mobile_no",
				"deal_owner",
				"modified",
			],
		)
		deals.append(deal.as_dict())

	return deals


@frappe.whitelist()
def create_new(contact: str, field: str, value: str):
	"""Create new email or phone for a contact"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	contact = frappe.get_cached_doc("Contact", contact)

	if field == "email":
		email = {"email_id": value, "is_primary": 1 if len(contact.email_ids) == 0 else 0}
		contact.append("email_ids", email)
	elif field in ("mobile_no", "phone"):
		mobile_no = {"phone": value, "is_primary_mobile_no": 1 if len(contact.phone_nos) == 0 else 0}
		contact.append("phone_nos", mobile_no)
	else:
		frappe.throw(_("Invalid field"))

	contact.save()
	return True


@frappe.whitelist()
def set_as_primary(contact: str, field: str, value: str):
	"""Set email or phone as primary for a contact"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	contact = frappe.get_doc("Contact", contact)

	if field == "email":
		for email in contact.email_ids:
			if email.email_id == value:
				email.is_primary = 1
			else:
				email.is_primary = 0
	elif field in ("mobile_no", "phone"):
		name = "is_primary_mobile_no" if field == "mobile_no" else "is_primary_phone"
		for phone in contact.phone_nos:
			if phone.phone == value:
				phone.set(name, 1)
			else:
				phone.set(name, 0)
	else:
		frappe.throw(_("Invalid field"))

	contact.save()
	return True


@frappe.whitelist()
def search_emails(txt: str):
	doctype = "Contact"
	meta = frappe.get_meta(doctype)
	filters = [["Contact", "email_id", "is", "set"]]

	if meta.get("fields", {"fieldname": "enabled", "fieldtype": "Check"}):
		filters.append([doctype, "enabled", "=", 1])
	if meta.get("fields", {"fieldname": "disabled", "fieldtype": "Check"}):
		filters.append([doctype, "disabled", "!=", 1])

	or_filters = []
	search_fields = ["full_name", "email_id", "name"]
	if txt:
		for f in search_fields:
			or_filters.append([doctype, f.strip(), "like", f"%{txt}%"])

	results = frappe.get_list(
		doctype,
		filters=filters,
		fields=search_fields,
		or_filters=or_filters,
		limit_start=0,
		limit_page_length=20,
		order_by="email_id, full_name, name",
		ignore_permissions=False,
		as_list=True,
		strict=False,
	)

	return results


CONTACT_TAB_MAX_PAGE_LENGTH = 100
CONTACT_TAB_KEYS = ("name", "label", "icon", "doctype", "columns")
# names of the contact page's own tabs (desktop and mobile), compared case-insensitively
RESERVED_CONTACT_TAB_NAMES = ("details", "deals")


def get_contact_tab_hooks() -> list[dict]:
	"""Valid tab descriptors declared by installed apps under the `crm_contact_tabs` hook.

	A descriptor without `name` or `method`, with a reserved or duplicate `name`, or
	whose `doctype` does not exist is skipped with a log line.
	"""
	tabs, seen = [], set()
	for tab in frappe.get_hooks("crm_contact_tabs"):
		name = tab.get("name")
		problem = None
		if not name or not tab.get("method"):
			problem = "needs a name and a method"
		elif name.lower() in RESERVED_CONTACT_TAB_NAMES:
			problem = "uses a reserved name"
		elif name in seen:
			problem = "repeats a name declared before it"
		elif tab.get("doctype") and not frappe.db.exists("DocType", tab["doctype"]):
			problem = "names a DocType that does not exist"
		if problem:
			frappe.logger("crm").warning(f"crm_contact_tabs: skipped tab {name!r}: it {problem}")
			continue
		seen.add(name)
		tabs.append({**tab, "columns": tab.get("columns") or []})
	return tabs


def _check_contact_permission(contact: str) -> None:
	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def _can_read_tab(tab: dict) -> bool:
	return not tab.get("doctype") or frappe.has_permission(tab["doctype"], "read")


@frappe.whitelist()
def get_contact_tabs(contact: str) -> list[dict]:
	"""Extra tabs for the contact page, after Deals, from the `crm_contact_tabs` hook.

	A tab whose `doctype` the user cannot read is left out. The provider `method`
	never leaves the server: rows are fetched through `get_contact_tab_rows`.
	"""
	_check_contact_permission(contact)
	return [
		{key: tab.get(key) for key in CONTACT_TAB_KEYS}
		for tab in get_contact_tab_hooks()
		if _can_read_tab(tab)
	]


@frappe.whitelist()
def get_contact_tab_rows(contact: str, tab: str, start: int = 0, page_length: int = 20) -> dict:
	"""One page of rows for a hook-declared contact tab.

	`tab` is resolved by name from the hooks only, so a client cannot call any
	other method. The provider is called as `method(contact=, start=, page_length=)`
	and returns `{"rows": [...], "total_count": n}`.
	"""
	_check_contact_permission(contact)

	descriptor = next((t for t in get_contact_tab_hooks() if t["name"] == tab), None)
	if not descriptor:
		frappe.throw(_("Contact tab {0} not found").format(tab), frappe.DoesNotExistError)
	if not _can_read_tab(descriptor):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	start = max(frappe.utils.cint(start), 0)
	page_length = min(max(frappe.utils.cint(page_length), 1), CONTACT_TAB_MAX_PAGE_LENGTH)

	result = frappe.get_attr(descriptor["method"])(contact=contact, start=start, page_length=page_length)
	rows = [_format_tab_row(row, descriptor["columns"]) for row in result.get("rows") or []]
	return {"rows": rows, "total_count": frappe.utils.cint(result.get("total_count"))}


def is_same_origin_path(url) -> bool:
	"""A path on this site: starts with one "/", no backslash, no whitespace or control character.

	Browsers read a backslash as "/" and drop tabs and newlines, so a path such as
	slash-backslash-host or slash-tab-slash-host would open another site.
	"""
	return (
		isinstance(url, str)
		and url.startswith("/")
		and not url.startswith("//")
		and "\\" not in url
		and all(ord(char) > 0x20 and ord(char) != 0x7F for char in url)
	)


def _format_tab_row(row: dict, columns: list[dict]) -> dict:
	row = frappe._dict(row)
	formatted = dict(row)
	for column in columns:
		fieldtype = column.get("fieldtype")
		if fieldtype and row.get(column["key"]) is not None:
			df = frappe._dict(fieldtype=fieldtype, options=column.get("options"))
			if fieldtype == "Currency" and not df.options:
				df.options = "currency"
			formatted[column["key"]] = frappe.format_value(row[column["key"]], df, doc=row)
	if "url" in formatted and not is_same_origin_path(formatted["url"]):
		formatted.pop("url")
	return formatted
