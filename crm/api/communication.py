import frappe
from frappe import _

@frappe.whitelist()
def track_communication():
    """Create a communication record for phone/whatsapp tracking, ignoring standard permissions"""
    try:
        doc = frappe.get_doc(frappe.parse_json(frappe.form_dict.get("doc")))
        doc.insert(ignore_permissions=True)
        return doc
    except Exception as e:
        frappe.log_error("Error in track_communication", str(e))
        frappe.throw(_("Could not track communication: {0}").format(str(e))) 