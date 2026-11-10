import frappe


def execute():
	# Page headers are never captured, so a Headers-scoped rule could never match.
	frappe.db.set_value(
		"CRM Enrichment Rule", {"match_scope": "Headers"}, "match_scope", "Full Text", update_modified=False
	)
