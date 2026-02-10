import frappe

@frappe.whitelist()
def get_user_email_accounts():
    """Return emails of logged-in user only"""

    user = frappe.session.user

    user_email = frappe.db.get_value("User", user, "email") or user

    accounts = frappe.get_all(
        "Email Account",
        fields=["name", "email_id", "email_account_name"],
        filters={"email_id": user_email, "enable_outgoing": 1},
    )

    return accounts


