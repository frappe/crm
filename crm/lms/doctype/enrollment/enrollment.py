# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Enrollment(Document):
    def validate(self):
        self._validate_unique_enrollment()

    def _validate_unique_enrollment(self):
        filters = {
            "student": self.student,
            "course": self.course,
            "name": ["!=", self.name],
        }
        if frappe.db.exists("Enrollment", filters):
            frappe.throw(
                _("Student {0} is already enrolled in course {1}").format(
                    self.student, self.course
                )
            )
