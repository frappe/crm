import frappe

@frappe.whitelist()
def get_user_email_accounts():
    """Return outgoing Email Accounts linked to the logged-in user"""

    user = frappe.session.user

    # Main 
    main_email = frappe.db.get_value("User", user, "email") or user

    # Extra 
    extra_emails = frappe.get_all(
        "User Email",
        filters={"parent": user},
        pluck="email_id",
    )

    # Combine 
    all_user_emails = [main_email] + extra_emails

    # Fetch only outgoing accounts 
    accounts = frappe.get_all(
        "Email Account",
        fields=["name", "email_id", "email_account_name"],
        filters={
            "enable_outgoing": 1,
            "email_id": ["in", all_user_emails],
        },
    )

    return accounts
