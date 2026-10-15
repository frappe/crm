import frappe


def execute():
	# rule_name is now built from the rule's target in before_validate; rename rows
	# saved with free text so they match. set_value skips validate, so sites that
	# already hold two rules for one target still migrate.
	for rule in frappe.get_all(
		"CRM Enrichment Rule", fields=["name", "rule_name", "rule_type", "target_value", "industry"]
	):
		target = rule.target_value if rule.rule_type == "Social" else rule.industry
		rule_name = f"{rule.rule_type}: {target}"
		if target and rule.rule_name != rule_name:
			frappe.db.set_value(
				"CRM Enrichment Rule", rule.name, "rule_name", rule_name, update_modified=False
			)
