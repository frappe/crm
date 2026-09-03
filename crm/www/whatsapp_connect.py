# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Hub-hosted WhatsApp Embedded Signup page.

Reached from a client CRM with a signed `state`; the page itself is public
because the visitor is logged into their own site, not into the hub. Nothing
sensitive is rendered: the state only says which site started the flow, and
`complete_signup` verifies its signature again server-side.
"""

import frappe
from frappe import _

from crm.integrations.meta.client import get_app_id
from crm.integrations.whatsapp.signup import allowed_site, config_id, parse_state

no_cache = 1


def get_context(context):
	context.no_cache = 1
	context.state = frappe.form_dict.get("state") or ""
	parsed = parse_state(context.state)

	context.app_id = get_app_id()
	context.config_id = config_id()
	context.site_label = ""
	context.error = ""

	if not parsed:
		context.error = _(
			"This connection link is invalid or has expired. Go back to your CRM and press Connect again."
		)
	elif not allowed_site(parsed["site"]):
		context.error = _("This site is not allowed to connect WhatsApp.")
	elif not context.app_id or not context.config_id:
		context.error = _("WhatsApp signup is not configured on this hub yet.")
	else:
		context.site_label = parsed["site"]
		context.return_url = parsed["site"] + "/crm?settings=WhatsApp"
	return context
