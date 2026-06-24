import frappe
from frappe import _
from frappe.model.document import Document


class LectureProgress(Document):
    def before_insert(self):
        self._set_completed_at()
        self._link_enrollment()

    def validate(self):
        self._set_completed_at()

    def on_update(self):
        self._update_enrollment_progress()

    def _set_completed_at(self):
        if self.status == "Completed" and not self.completed_at:
            self.completed_at = frappe.utils.now_datetime()

    def _link_enrollment(self):
        if self.enrollment:
            return
        enrollment = frappe.get_all(
            "Enrollment",
            filters={"student": self.student, "course": self.course, "status": "Active"},
            limit=1,
            pluck="name",
        )
        if enrollment:
            self.enrollment = enrollment[0]

    def _update_enrollment_progress(self):
        if self.status != "Completed" or not self.enrollment:
            return
        enrollment = frappe.get_doc("Enrollment", self.enrollment)
        completed = frappe.db.count(
            "Lecture Progress",
            {"enrollment": self.enrollment, "status": "Completed"},
        )
        total = enrollment.total_lessons or frappe.db.count("Course Lecture", {"course": enrollment.course})
        enrollment.completed_lessons = completed
        if total > 0 and completed >= total:
            enrollment.status = "Completed"
        if not frappe.has_permission("Enrollment", "write", user=frappe.session.user):
            frappe.throw(_("Insufficient permissions to update enrollment"))
        enrollment.save()
