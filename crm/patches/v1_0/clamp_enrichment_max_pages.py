import frappe

from crm.domain_enrichment.config import MAX_PAGES_LIMIT


def execute():
	# max_pages had no upper bound before; a stored value above the limit would
	# fail every later save of CRM Enrichment Settings.
	max_pages = frappe.db.get_single_value("CRM Enrichment Settings", "max_pages")
	if max_pages and max_pages > MAX_PAGES_LIMIT:
		frappe.db.set_single_value("CRM Enrichment Settings", "max_pages", MAX_PAGES_LIMIT)
