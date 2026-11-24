from urllib.parse import urlencode, urlsplit

import frappe
from frappe import _
from frappe.utils import get_url


@frappe.whitelist(methods=["GET"])
def return_to_connector(return_to: str):
	"""Send a user who signed in from an AI app back to it, with this site's address."""
	if not is_connector_host(return_to):
		frappe.throw(_("This app cannot connect to your CRM."), frappe.PermissionError)

	site = urlsplit(get_url()).netloc
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = (
		f"{return_to}{'&' if '?' in return_to else '?'}{urlencode({'site': site})}"
	)


def is_connector_host(url: str) -> bool:
	"""Only https hosts listed in the `connector_hosts` site config."""
	parts = urlsplit(url)
	return parts.scheme == "https" and parts.netloc in (frappe.conf.get("connector_hosts") or [])
