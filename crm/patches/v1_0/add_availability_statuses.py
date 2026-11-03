from crm.install import add_availability_user_fields, add_default_availability_statuses


def execute():
	add_default_availability_statuses()
	add_availability_user_fields()
