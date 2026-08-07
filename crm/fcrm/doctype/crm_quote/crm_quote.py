import frappe
from frappe.model.document import Document


class CRMQuote(Document):
	# begin: auto-generated types
	from typing import TYPE_CHECKING
	if TYPE_CHECKING:
		from frappe.types import DF
		deal: DF.Link
		customer: DF.Link | None
		partner: DF.Link | None
		quote_date: DF.Date
		valid_until: DF.Date | None
		contract_start_date: DF.Date | None
		payment_terms: DF.Literal["Annual Upfront", "Quarterly Advance", "Monthly"]
		contract_term_yrs: DF.Int
		currency: DF.Link | None
		previous_version: DF.Link | None
		submitted_by: DF.Link | None
		status: DF.Literal["Draft", "Sent", "Accepted", "Rejected"]
		erpnext_sales_invoice: DF.Data | None
		subtotal_excl_vat: DF.Currency
		discount_applied: DF.Currency
		vat_amount: DF.Currency
		grand_total: DF.Currency
		notes: DF.LongText | None
		terms_and_conditions: DF.LongText | None
	# end: auto-generated types

	def before_insert(self):
		if not self.quote_date:
			self.quote_date = frappe.utils.nowdate()
		if not self.valid_until:
			self.valid_until = frappe.utils.add_days(self.quote_date, 30)
		if not self.submitted_by:
			self.submitted_by = frappe.session.user
		self._populate_deal_fields()

	def _populate_deal_fields(self):
		if not self.deal:
			return
		if not self.customer:
			self.customer = frappe.db.get_value("CRM Deal", self.deal, "organization") or ""
