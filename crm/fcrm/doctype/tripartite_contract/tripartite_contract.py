from frappe.model.document import Document


class TripartiteContract(Document):
	def validate(self):
		self.remaining_credit = (self.credit_limit or 0) - (self.current_debt or 0)
		self.credit_locked = 1 if (self.current_debt or 0) >= (self.credit_limit or 0) else 0
