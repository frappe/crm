import frappe
from frappe import _


@frappe.whitelist()
def get_address(name):
    Address = frappe.qb.DocType("Address")

    query = frappe.qb.from_(Address).select("*").where(Address.name == name).limit(1)

    address = query.run(as_dict=True)
    if not len(address):
        frappe.throw(_("Address not found"), frappe.DoesNotExistError)
    address = address.pop()

    address["doctype"] = "Address"
    return address


@frappe.whitelist()
def get_linked_address(link_doctype, link_name=None):
    dict_list = frappe.get_list(
        "Dynamic Link",
        [
            ["parenttype", "=", "Address"],
            ["link_doctype", "=", link_doctype],
            ["link_name", "=", link_name],
        ],
    )

    names = []
    for dict in dict_list:
        doc = frappe.get_doc("Dynamic Link", dict.name)
        names.append(doc.parent)

    return names


@frappe.whitelist()
def get_linked_docs(address, link_doctype=None):
    dict_list = frappe.get_list(
        "Dynamic Link",
        [
            ["parenttype", "=", "Address"],
            ["link_doctype", "=", link_doctype],
            ["parent", "=", address],
        ],
    )

    names = []
    for dict in dict_list:
        doc = frappe.get_doc("Dynamic Link", dict.name)
        names.append(doc.link_name)
