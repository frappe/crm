# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def _find_active_abonement(student):
    """FIFO: find oldest active abonement with remaining classes."""
    abonements = frappe.get_all(
        "Student Abonement",
        filters={
            "student": student,
            "status": "Active",
            "classes_remaining": [">", 0],
        },
        fields=["name", "classes_remaining", "end_date"],
        order_by="start_date asc",
        limit=1,
    )
    return abonements[0] if abonements else None


def adjust_abonement_on_attendance(doc, method):
    """Hook on Student Attendance validate — FIFO deduction / restore.

    Cases:
    - New record with Present/Late → deduct from oldest active abonement.
    - Existing record changed from Absent→Present/Late → deduct.
    - Existing record changed from Present/Late→Absent → restore.
    - Frozen/Expired → skip deduction, throw if no active abonement found.
    """
    if frappe.flags.in_patch or frappe.flags.in_install:
        return

    is_present = doc.status in ("Present", "Late")
    is_absent = doc.status in ("Absent", "Excused")

    old = doc.get_doc_before_save()

    # Determine if status actually changed
    if old and old.status == doc.status:
        return

    was_present = old and old.status in ("Present", "Late")

    if is_present and not was_present:
        # Deduct one class from oldest active abonement
        ab = _find_active_abonement(doc.student)
        if not ab:
            frappe.throw(
                _(
                    "Student {0} has no active abonement with available classes. "
                    "Please purchase or activate an abonement first."
                ).format(doc.student)
            )

        ab_doc = frappe.get_doc("Student Abonement", ab.name)
        ab_doc.classes_remaining = ab.classes_remaining - 1
        if ab_doc.classes_remaining <= 0:
            ab_doc.status = "Expired"
        ab_doc.save(ignore_permissions=True)

        doc.linked_abonement = ab.name

    elif was_present and is_absent:
        # Restore one class to the linked abonement
        linked = doc.linked_abonement
        if not linked:
            return

        ab = frappe.get_doc("Student Abonement", linked)
        if ab.status == "Expired":
            ab.status = "Active"
        ab.classes_remaining = (ab.classes_remaining or 0) + 1
        ab.save(ignore_permissions=True)

        doc.linked_abonement = None


@frappe.whitelist()
def check_abonement_balance(student=None):
    if not student:
        students = frappe.get_all("Student", filters={"user": frappe.session.user}, limit=1)
        if not students:
            return {"available": False, "remaining": 0}
        student = students[0].name
    ab = _find_active_abonement(student)
    if not ab:
        return {"available": False, "remaining": 0}

    doc = frappe.get_doc("Student Abonement", ab.name)
    return {
        "available": True,
        "remaining": doc.classes_remaining,
        "abonement_name": doc.name,
        "abonement_type": doc.abonement_type,
        "end_date": doc.end_date,
    }
