import frappe
from frappe import _

VOIDABLE = {"CRM Quotation", "CRM Lead", "CRM Deal"}


@frappe.whitelist()
def void_document(doctype: str, name: str, void: int = 1, reason: str | None = None):
    """Tandai dokumen sebagai void (soft-cancel) atau batalkan void. Reversible."""
    if doctype not in VOIDABLE:
        frappe.throw(_("Void is not supported for {0}").format(doctype))
    if not frappe.has_permission(doctype, "write", name):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    void = int(void)
    doc = frappe.get_doc(doctype, name)
    doc.is_void = void
    if void:
        doc.void_reason = reason
        doc.void_at = frappe.utils.now()
        doc.void_by = frappe.session.user
    else:
        doc.void_reason = None
        doc.void_at = None
        doc.void_by = None
    doc.save(ignore_permissions=True)

    return {
        "is_void": doc.is_void,
        "void_by": doc.void_by,
        "void_at": doc.void_at,
        "void_reason": doc.void_reason,
    }
