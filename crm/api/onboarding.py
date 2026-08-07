import frappe


@frappe.whitelist(allow_guest=False)
def provisioning_complete(deal):
    """Called by CareVerse HQ when Org Account + Facility License are provisioned."""
    if "System Manager" not in frappe.get_roles(frappe.session.user) and frappe.session.user != "Administrator":
        frappe.throw("Unauthorized", frappe.PermissionError)
    req = frappe.get_list(
        "CRM Onboarding Request",
        filters={"deal": deal},
        fields=["name"],
        limit=1,
    )
    if not req:
        frappe.throw("No Onboarding Request for deal %s" % deal)
    doc = frappe.get_doc("CRM Onboarding Request", req[0].name)
    doc.careverse_provisioned_date = frappe.utils.nowdate()
    doc.status = "Complete"
    doc.save()
    return {"status": "complete", "onboarding_request": doc.name}


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
