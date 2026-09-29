import frappe


@frappe.whitelist()
def get_first_lead(name: str | None = None):
	# prefer the lead the user created during onboarding, if it still exists, is unconverted
	# and the user can still read it
	if name and frappe.get_list("CRM Lead", filters={"name": name, "converted": 0}, pluck="name", limit=1):
		return name

	lead = frappe.get_list(
		"CRM Lead",
		filters={"converted": 0},
		pluck="name",
		order_by="creation",
		limit=1,
	)
	return lead[0] if lead else None


@frappe.whitelist()
def get_first_deal(name: str | None = None):
	# prefer the deal the user created during onboarding, if it still exists and the user can still read it
	if name and frappe.get_list("CRM Deal", filters={"name": name}, pluck="name", limit=1):
		return name

	deal = frappe.get_list(
		"CRM Deal",
		pluck="name",
		order_by="creation",
		limit=1,
	)
	return deal[0] if deal else None
