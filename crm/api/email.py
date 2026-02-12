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
        order_by="idx",
    )

    # Combine
    all_user_emails = []
    if main_email and main_email not in extra_emails:
        all_user_emails.append(main_email)

    all_user_emails.extend(extra_emails)

    # Fetch only outgoing accounts
    accounts = frappe.get_all(
        "Email Account",
        fields=["name", "email_id", "email_account_name"],
        filters={
            "enable_outgoing": 1,
            "email_id": ["in", all_user_emails],
        },
    )

    # Sort
    email_priority = {email.lower(): idx for idx, email in enumerate(all_user_emails) if email}

    accounts.sort(key=lambda x: email_priority.get((x.email_id or "").lower(), 9999))

    return accounts
