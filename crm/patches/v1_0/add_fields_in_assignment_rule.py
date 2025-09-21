from crm.install import (
	add_assignment_rule_property_setters,
	create_assignment_rule_custom_fields,
)


def execute():
	create_assignment_rule_custom_fields()
	add_assignment_rule_property_setters()
