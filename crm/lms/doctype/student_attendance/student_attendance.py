# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class StudentAttendance(Document):
    def validate(self):
        self._validate_unique_attendance()

    def _validate_unique_attendance(self):
        filters = {
            "student": self.student,
            "academic_session": self.academic_session,
            "name": ["!=", self.name],
        }
        if frappe.db.exists("Student Attendance", filters):
            frappe.throw(
                _("Attendance already recorded for student {0} in this session").format(
                    self.student
                )
            )
