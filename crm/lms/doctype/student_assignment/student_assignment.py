# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class StudentAssignment(Document):
    def validate(self):
        self._validate_score()

    def _validate_score(self):
        if self.score is not None and (self.score < 0 or self.score > 100):
            frappe.throw(_("Score must be between 0 and 100"))
