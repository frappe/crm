from crm.install import add_default_view_all_roles


def execute():
	# Sales Manager sees every Lead and Deal today; make that explicit in FCRM Settings.
	add_default_view_all_roles()
