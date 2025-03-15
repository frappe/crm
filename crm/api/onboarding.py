import json

import frappe


@frappe.whitelist()
def update_user_onboarding_status(steps: str):
	steps = json.loads(steps)

	# get the current onboarding status
	onboarding_status = frappe.db.get_value("User", frappe.session.user, "onboarding_status")
	onboarding_status = frappe.parse_json(onboarding_status)

	# update the onboarding status
	onboarding_status["frappe_crm_onboarding_status"] = steps

	frappe.db.set_value(
		"User", frappe.session.user, "onboarding_status", json.dumps(onboarding_status), update_modified=False
	)


@frappe.whitelist()
def get_first_lead():
	lead = frappe.get_all(
		"CRM Lead",
		filters={"converted": 0},
		fields=["name"],
		order_by="creation",
		limit=1,
	)
	return lead[0].name if lead else None


@frappe.whitelist()
def get_first_deal():
	deal = frappe.get_all(
		"CRM Deal",
		fields=["name"],
		order_by="creation",
		limit=1,
	)
	return deal[0].name if deal else None
