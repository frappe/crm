# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class AcademicSession(Document):
    def validate(self):
        self._set_title()
        self._validate_no_overlap()

    def _set_title(self):
        if not self.title:
            self.title = f"{self.group} - {self.date}"

    def _validate_no_overlap(self):
        filters = {
            "group": self.group,
            "date": self.date,
            "start_time": ["<", self.end_time],
            "end_time": [">", self.start_time],
            "name": ["!=", self.name],
        }
        if frappe.db.exists("Academic Session", filters):
            frappe.throw(
                _("Time slot overlaps with another session for this group on {0}").format(
                    self.date
                )
            )
