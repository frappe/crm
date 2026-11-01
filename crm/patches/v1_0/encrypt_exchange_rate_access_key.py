import frappe
from frappe.utils.password import set_encrypted_password

from crm.patches.v1_0.encrypt_twilio_api_secret import is_mask, mask_versions

DOCTYPE = "FCRM Settings"


def execute():
	key = frappe.db.get_single_value(DOCTYPE, "access_key")
	if key and not is_mask(key):
		set_encrypted_password(DOCTYPE, DOCTYPE, key, "access_key")
		frappe.db.set_single_value(DOCTYPE, "access_key", "*" * len(key))

	mask_versions(DOCTYPE, "access_key")
