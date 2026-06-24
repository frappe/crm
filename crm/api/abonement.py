import frappe
from frappe import _
from frappe.model.document import Document


def _assert_student_ownership(student: str) -> None:
    student_user = frappe.db.get_value("Student", student, "user")
    if student_user and student_user != frappe.session.user:
        if "Instructor" not in frappe.get_roles():
            frappe.throw(_("Not permitted to view this student's data"), frappe.PermissionError)


def _find_active_abonement(student: str) -> dict | None:
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


def adjust_abonement_on_attendance(doc: Document, method: str) -> None:
    if frappe.flags.in_patch or frappe.flags.in_install:
        return

    is_present = doc.status in ("Present", "Late")
    is_absent = doc.status in ("Absent", "Excused")

    old = doc.get_doc_before_save()

    if old and old.status == doc.status:
        return

    was_present = old and old.status in ("Present", "Late")

    if is_present and not was_present:
        ab = _find_active_abonement(doc.student)
        if not ab:
            frappe.throw(
                _(
                    "Student {0} has no active abonement with available classes. "
                    "Please purchase or activate an abonement first."
                ).format(doc.student)
            )

        ab_doc = frappe.get_doc("Student Abonement", ab.name)
        if not frappe.has_permission("Student Abonement", "write", user=frappe.session.user):
            frappe.throw(_("Insufficient permissions to modify abonement"))
        ab_doc.classes_remaining = ab.classes_remaining - 1
        if ab_doc.classes_remaining <= 0:
            ab_doc.status = "Expired"
        ab_doc.save()

        doc.linked_abonement = ab.name

    elif was_present and is_absent:
        linked = doc.linked_abonement
        if not linked:
            return

        ab = frappe.get_doc("Student Abonement", linked)
        if not frappe.has_permission("Student Abonement", "write", user=frappe.session.user):
            frappe.throw(_("Insufficient permissions to modify abonement"))
        if ab.status == "Expired":
            ab.status = "Active"
        ab.classes_remaining = (ab.classes_remaining or 0) + 1
        ab.save()

        doc.linked_abonement = None


@frappe.whitelist()
def check_abonement_balance(student: str | None = None) -> dict:
    if not student:
        students = frappe.get_all("Student", filters={"user": frappe.session.user}, limit=1)
        if not students:
            return {"available": False, "remaining": 0}
        student = students[0].name
    else:
        _assert_student_ownership(student)
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
