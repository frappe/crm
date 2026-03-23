import json

import frappe

DEMO_STATE_KEY = "crm_demo_data_created"
DEMO_LEADS_KEY = "crm_demo_leads"


def create_demo_data():
	if frappe.db.get_default(DEMO_STATE_KEY):
		return

	from crm.demo.leads import create_demo_leads

	lead_names = create_demo_leads()
	frappe.db.set_default(DEMO_LEADS_KEY, json.dumps(lead_names))
	frappe.db.set_default(DEMO_STATE_KEY, "1")


@frappe.whitelist()
def clear_demo_data():
	if not frappe.db.get_default(DEMO_STATE_KEY):
		return

	from crm.demo.leads import delete_demo_leads

	lead_names_raw = frappe.db.get_default(DEMO_LEADS_KEY)
	if lead_names_raw:
		delete_demo_leads(json.loads(lead_names_raw))

	frappe.db.set_default(DEMO_LEADS_KEY, None)
	frappe.db.set_default(DEMO_STATE_KEY, None)


@frappe.whitelist()
def get_demo_state():
	return {"demo_data_created": bool(frappe.db.get_default(DEMO_STATE_KEY))}
