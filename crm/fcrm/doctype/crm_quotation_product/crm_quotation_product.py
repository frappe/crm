import frappe
from frappe.model.document import Document


class CRMQuotationProduct(Document):
    def validate(self):
        # Auto calculate amount = qty * price
        self.amount = (self.qty or 0) * (self.price or 0)