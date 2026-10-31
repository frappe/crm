import json

import frappe

from crm.fcrm.doctype.crm_twilio_settings.crm_twilio_settings import store_api_secret

DOCTYPE = "CRM Twilio Settings"


def execute():
	secret = frappe.db.get_single_value(DOCTYPE, "api_secret")
	if secret and not is_mask(secret):
		frappe.db.set_single_value(DOCTYPE, "api_secret", store_api_secret(secret))

	mask_versions()


def mask_versions():
	"""The old controller's key change was tracked too, so its Version rows hold the plain secret."""
	for name, data in frappe.get_all("Version", {"ref_doctype": DOCTYPE}, ["name", "data"], as_list=True):
		changes = json.loads(data or "{}")
		changed = [row for row in changes.get("changed", []) if row[0] == "api_secret"]
		if not any(value and not is_mask(value) for row in changed for value in row[1:]):
			continue

		for row in changed:
			row[1:] = [value and "*" * len(value) for value in row[1:]]
		frappe.db.set_value("Version", name, "data", json.dumps(changes), update_modified=False)


def is_mask(value: str) -> bool:
	return set(value) == {"*"}
