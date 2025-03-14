import frappe


@frappe.whitelist()
def get_users():
    users = frappe.qb.get_query(
        "User",
        fields=[
            "name",
            "email",
            "enabled",
            "user_image",
            "first_name",
            "last_name",
            "full_name",
            "user_type",
        ],
        filters={"user_type": "System User"},
        order_by="full_name asc",
        distinct=True,
    ).run(as_dict=1)

    for user in users:
        if frappe.session.user == user.name:
            user.session_user = True

        user.is_manager = (
            "Sales Manager" in frappe.get_roles(user.name)
            or user.name == "Administrator"
        )
    return users


@frappe.whitelist()
def get_contacts():
    from itertools import chain

    def get_contact_data(filters: dict = None):
        contacts = get_contact_list(filters)
        contact_names = [c.name for c in contacts]
        contact_emails = get_contact_emails(contact_names)
        contact_phone = get_contact_phones(contact_names)
        for contact in contacts:
            contact.email_ids = [e for e in contact_emails if e.parent == contact.name]
            contact.phone_nos = [p for p in contact_phone if p.parent == contact.name]

        contact_name_set = {c.name for c in contacts}
        filtered_contact_names = list(
            {
                c.parent
                for c in chain(contact_emails, contact_phone)
                if c.parent not in contact_name_set
            }
        )
        return contacts, filtered_contact_names

    # Get contacts  from `tabContact` which has mobile number set.
    filters = {"mobile_no": ["is", "set"]}
    contacts_1, filtered_contact_names = get_contact_data(filters)

    # Get list of contacts to be fetched from  `tabContact Email` and `tabContact Phone` combine them, and finally fetch the contacts.
    filters.update({"name": ["in", filtered_contact_names]})
    contacts_2, _ = get_contact_data(filters)

    # Combine the contacts from both the queries.
    return list(chain(contacts_1, contacts_2))


@frappe.whitelist()
def get_lead_contacts():
    lead_contacts = frappe.get_all(
        "Lead",
        fields=["name", "lead_name", "mobile_no", "phone", "image", "modified"],
        filters={"converted": 0},
        order_by="lead_name asc",
        distinct=True,
    )

    return lead_contacts


@frappe.whitelist()
def get_customers():
    customers = frappe.qb.get_query(
        "Customer",
        fields=["*"],
        order_by="name asc",
        distinct=True,
    ).run(as_dict=1)

    return customers


def get_contact_list(filters: dict = None):
    return frappe.get_all(
        "Contact",
        fields=[
            "name",
            "salutation",
            "first_name",
            "last_name",
            "full_name",
            "gender",
            "address",
            "designation",
            "image",
            "email_id",
            "mobile_no",
            "phone",
            "company_name",
            "modified",
        ],
        order_by="first_name asc",
        filters=filters,
        distinct=True,
    )


def get_contact_emails(parent_contact_names: list):
    return frappe.get_all(
        "Contact Email",
        filters={"parenttype": "Contact", "parent": ["in", parent_contact_names]},
        fields=["name", "email_id", "is_primary", "parent"],
    )


def get_contact_phones(parent_contact_names: list):
    return frappe.get_all(
        "Contact Phone",
        filters={"parenttype": "Contact", "parent": ["in", parent_contact_names]},
        fields=["name", "phone", "is_primary_phone", "is_primary_mobile_no", "parent"],
    )
