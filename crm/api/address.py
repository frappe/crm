import frappe
from frappe import _
from frappe.contacts.doctype.address.address import render_address
from frappe.utils import escape_html


@frappe.whitelist()
def get_address_display(name: str | None = None) -> str | None:
	"""Return the rendered HTML block for an Address.

	Annotations do not validate anything at runtime, so `name` is checked
	explicitly: it arrives straight off an HTTP request, and frappe treats a
	dict as a set of filters rather than a docname.
	"""
	if not isinstance(name, str) or not name:
		return None

	if not frappe.db.exists("Address", name):
		return None

	address = frappe.get_cached_doc("Address", name)
	address.check_permission()

	try:
		return render_address(address.as_dict(), check_permissions=False)
	except frappe.ValidationError:
		# render_address() throws when the site has no Address Template record
		# at all, which is the common case for CRM installs without ERPNext.
		frappe.clear_last_message()
		return render_without_template(address.as_dict())


def render_without_template(address: dict) -> str:
	"""Build a plain address block for sites that have no Address Template.

	Deliberately avoids frappe.render_template(): a rendered template is an
	SSTI sink, and nothing here needs one.
	"""
	lines = [
		address.get("address_line1"),
		address.get("address_line2"),
		address.get("city"),
		address.get("state"),
		address.get("pincode"),
		address.get("country"),
	]
	parts = [escape_html(line) for line in lines if line]

	for label, value in ((_("Phone"), address.get("phone")), (_("Email"), address.get("email_id"))):
		if value:
			parts.append(f"{escape_html(label)}: {escape_html(value)}")

	return "<br>\n".join(parts)
