# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days


class StudentAbonement(Document):
    def validate(self):
        self._set_end_date()

    def before_insert(self):
        self._init_remaining()

    def _set_end_date(self):
        if self.abonement_type and self.start_date:
            validity = frappe.db.get_value("Abonement Type", self.abonement_type, "validity_days")
            if validity:
                self.end_date = add_days(self.start_date, validity)

    def _init_remaining(self):
        if self.abonement_type and not self.classes_remaining:
            total = frappe.db.get_value("Abonement Type", self.abonement_type, "total_classes")
            self.classes_remaining = total or 0
