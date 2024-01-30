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
        _notifications.append(
            {
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
                "reference_doctype": "deal"
                if notification.reference_doctype == "CRM Deal"
                else "lead",
                "reference_name": notification.reference_name,
                "route_name": "Deal"
                if notification.reference_doctype == "CRM Deal"
                else "Lead",
            }
        )

    return _notifications


@frappe.whitelist()
def mark_as_read(user=None, comment=None):
    if frappe.session.user == "Guest":
        frappe.throw("Authentication failed", exc=frappe.AuthenticationError)

    user = user or frappe.session.user
    filters = {"to_user": user, "read": False}
    if comment:
        filters["comment"] = comment
    for n in frappe.get_all("CRM Notification", filters=filters):
        d = frappe.get_doc("CRM Notification", n.name)
        d.read = True
        d.save()
