import frappe


@frappe.whitelist()
def get_notifications():
    if frappe.session.user == "Guest":
        frappe.throw("Authentication failed", exc=frappe.AuthenticationError)

    Notification = frappe.qb.DocType("CRM Notification")
    query = (
        frappe.qb.from_(Notification)
        .select("*")
        .where(Notification.to_user == frappe.session.user)
        .where(Notification.read == False)
        .orderby("creation")
    )
    notifications = query.run(as_dict=True)
    return notifications
