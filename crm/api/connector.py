from urllib.parse import urlencode, urlsplit

import frappe
from frappe import _

GATEWAY_URL = "https://mcp.bom.frappe.cloud"
CLIENT_ID = "mcp-gateway"


@frappe.whitelist(methods=["GET"])
def return_to_connector(return_to: str):
	"""Send a user who signed in from an AI app back to the gateway, with this site's address."""
	if not is_gateway(return_to):
		frappe.throw(_("This app cannot connect to your CRM."), frappe.PermissionError)

	site = frappe.local.request.host
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = (
		f"{return_to}{'&' if '?' in return_to else '?'}{urlencode({'site': site})}"
	)


def gateway_url() -> str:
	"""The MCP gateway for ChatGPT and Claude. `mcp_gateway_url` in site config points a test site elsewhere."""
	return (frappe.conf.get("mcp_gateway_url") or GATEWAY_URL).rstrip("/")


def is_gateway(url: str) -> bool:
	parts, gateway = urlsplit(url), urlsplit(gateway_url())
	return (parts.scheme, parts.netloc) == (gateway.scheme, gateway.netloc)


def ensure_gateway_client():
	"""The public OAuth client the gateway signs users in with. Its only redirect is the gateway,
	so no other app can receive its codes."""
	redirect_uri = f"{gateway_url()}/site/callback"
	if frappe.db.get_value("OAuth Client", CLIENT_ID, "redirect_uris") == redirect_uri:
		return

	values = {
		"app_name": "ChatGPT and Claude",
		"redirect_uris": redirect_uri,
		"default_redirect_uri": redirect_uri,
		"grant_type": "Authorization Code",
		"response_type": "Code",
		"token_endpoint_auth_method": "None",
		"scopes": "all",
		"skip_authorization": 0,
	}
	if frappe.db.exists("OAuth Client", CLIENT_ID):
		frappe.get_doc("OAuth Client", CLIENT_ID).update(values).save(ignore_permissions=True)
	else:
		frappe.get_doc({"doctype": "OAuth Client", **values}).insert(
			ignore_permissions=True, set_name=CLIENT_ID
		)
