# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from next_crm.install import after_install


class NCRMSettings(Document):
    @frappe.whitelist()
    def restore_defaults(self, force=False):
        after_install(force)
