import frappe
from frappe.utils import cint

# A copy of config.MAX_PAGES_LIMIT, kept here so a later rename there can't
# break migrate on sites that haven't run this patch yet.
MAX_PAGES_LIMIT = 20


def execute():
	# max_pages had no bounds before; a stored value outside 1..MAX_PAGES_LIMIT
	# would fail every later save of CRM Enrichment Settings. Read raw, since
	# get_single_value casts an unset Int to 0, and unset falls back to the default.
	max_pages = frappe.db.get_singles_dict("CRM Enrichment Settings").get("max_pages")
	if max_pages in (None, ""):
		return
	clamped = min(max(cint(max_pages), 1), MAX_PAGES_LIMIT)
	if clamped != cint(max_pages):
		frappe.db.set_single_value("CRM Enrichment Settings", "max_pages", clamped)
