import frappe
from frappe.query_builder import DocType


def execute():
	"""Keep is_duplicate in step with merged_into on CRM Leads.

	Duplicate matching and the merge picker skip is_duplicate leads, while phone
	matching follows merged_into, so the two must agree. A fresh column already
	defaults every lead to is_duplicate 0 and no merged_into; this only fixes leads
	where they disagree, so it is safe to run again.
	"""
	lead = DocType("CRM Lead")
	merged = lead.merged_into.isnotnull() & (lead.merged_into != "")

	frappe.qb.update(lead).set(lead.is_duplicate, 1).where(merged & (lead.is_duplicate != 1)).run()
	frappe.qb.update(lead).set(lead.is_duplicate, 0).where(
		~merged & (lead.is_duplicate.isnull() | (lead.is_duplicate != 0))
	).run()
