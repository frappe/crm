import frappe
from frappe.query_builder import Order

@frappe.whitelist()
def get_notifications():
    if frappe.session.user == "Guest":
        frappe.throw("Authentication failed", exc=frappe.AuthenticationError)

    Notification = frappe.qb.DocType("CRM Notification")
    query = (
        frappe.qb.from_(Notification)
        .select("*")
        .where(Notification.to_user == frappe.session.user)
        .orderby("creation", order=Order.desc)
    )
    notifications = query.run(as_dict=True)

    _notifications = []
    for notification in notifications:
        reference_doc = frappe.get_value("Comment", notification.comment, ['reference_doctype', 'reference_name'])
        _notifications.append({
            "creation": notification.creation,
            "from_user": {
                "name": notification.from_user,
                "full_name": frappe.get_value(
                    "User", notification.from_user, "full_name"
                ),
            },
            "type": notification.type,
            "to_user": notification.to_user,
            "read": notification.read,
            "comment": notification.comment,
            "reference_doctype": "deal" if reference_doc[0] == "CRM Deal" else "lead",
            "reference_name": reference_doc[1],
            "route_name": "Deal" if reference_doc[0] == "CRM Deal" else "Lead",
        })

    return _notifications
