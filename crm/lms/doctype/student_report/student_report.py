# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class StudentReport(Document):
    def before_validate(self):
        if not self.student_name:
            name = frappe.db.get_value("Student", self.student, "student_name")
            self.student_name = name
