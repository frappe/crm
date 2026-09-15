from crm.install import set_default_currency


def execute():
	# Sites that never picked a CRM currency were silently falling back to USD;
	# seed it from the currency chosen in the setup wizard instead.
	set_default_currency()
