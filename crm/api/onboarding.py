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


_VALID_APPROVER_SLOTS = ("network_approver_1", "network_approver_2", "tiberbu_approver")


@frappe.whitelist()
def approve_onboarding(
    onboarding_request: str,
    approver_slot: str,
    reject: int = 0,
    rejection_reason: str = "",
) -> dict:
    """
    approver_slot: "network_approver_1" | "network_approver_2" | "tiberbu_approver"
    reject: 1 to reject, 0 to approve
    Returns: {approval_status, onboarding_request}
    """
    if approver_slot not in _VALID_APPROVER_SLOTS:
        frappe.throw(
            "Invalid approver_slot '%s'. Must be one of: %s"
            % (approver_slot, ", ".join(_VALID_APPROVER_SLOTS))
        )

    doc = frappe.get_doc("CRM Onboarding Request", onboarding_request)

    nominated = doc.get(approver_slot)
    if nominated != frappe.session.user:
        frappe.throw(
            "You are not the nominated approver for this slot.",
            frappe.PermissionError,
        )

    if doc.approval_status in ("Approved", "Rejected"):
        frappe.throw(
            "This onboarding request is already %s and cannot be updated."
            % doc.approval_status
        )

    if frappe.utils.cint(reject):
        doc.approval_status = "Rejected"
        doc.rejection_reason = rejection_reason
        doc.flags.ignore_permissions = True  # SYSTEM-INTERNAL
        doc.save()
        return {"approval_status": "Rejected", "onboarding_request": doc.name}

    # Approve path
    doc.set(approver_slot + "_approved", 1)
    doc.set(approver_slot + "_at", frappe.utils.now_datetime())

    all_approved = (
        doc.network_approver_1_approved
        and doc.network_approver_2_approved
        and doc.tiberbu_approver_approved
    )
    any_approved = (
        doc.network_approver_1_approved
        or doc.network_approver_2_approved
        or doc.tiberbu_approver_approved
    )

    if all_approved:
        doc.approval_status = "Approved"
    elif any_approved:
        doc.approval_status = "Partially Approved"
    # else: remains "Pending"

    doc.flags.ignore_permissions = True  # SYSTEM-INTERNAL
    doc.save()

    return {"approval_status": doc.approval_status, "onboarding_request": doc.name}


@frappe.whitelist()
def reject_onboarding(
    onboarding_request: str,
    approver_slot: str,
    rejection_reason: str = "",
) -> dict:
    return approve_onboarding(
        onboarding_request, approver_slot, reject=1, rejection_reason=rejection_reason
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
