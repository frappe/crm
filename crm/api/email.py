import frappe
from frappe import _


@frappe.whitelist()
def get_user_email_accounts():
    """Return outgoing Email Accounts linked to the logged-in user."""
    if not any(
        role in ["Sales User", "Sales Manager", "System Manager"]
        for role in frappe.get_roles()
    ):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    user = frappe.session.user

    # Get the user's primary email
    main_email = frappe.db.get_value("User", user, "email") or user

    # Get additional email addresses linked to the user
    extra_emails = frappe.get_all(
        "User Email",
        filters={"parent": user},
        pluck="email_id",
    )

    # Combine all user emails
    all_user_emails = [main_email] + extra_emails

    # Fetch only outgoing email accounts matching the user's emails
    accounts = frappe.get_all(
        "Email Account",
        fields=["name", "email_id", "email_account_name"],
        filters={
            "enable_outgoing": 1,
            "email_id": ["in", all_user_emails],
        },
        order_by="email_account_name asc",
    )

    return accounts
