import frappe


def complete_setup_for_fc_site(login_manager=None):
	"""Finish setup with the data Frappe Cloud prefilled at signup, so the desk wizard is skipped."""
	if not should_auto_complete_setup():
		return

	from frappe.desk.page.setup_wizard.setup_wizard import setup_complete

	try:
		setup_complete(get_prefilled_setup_args())
	except Exception:
		frappe.log_error("Frappe Cloud setup auto-complete failed")


def should_auto_complete_setup():
	from frappe.core.doctype.installed_applications.installed_applications import has_non_admin_user
	from frappe.integrations.frappe_providers.frappecloud_billing import is_fc_site

	if frappe.is_setup_complete() or frappe.conf.skip_setup_wizard:
		return False
	# apps with their own wizard stages (e.g. ERPNext) still need user input
	if frappe.get_hooks("setup_wizard_stages"):
		return False
	return has_non_admin_user() and is_fc_site()


def get_prefilled_setup_args():
	settings = frappe.get_single("System Settings")
	language = frappe.db.get_value("Language", settings.language, "language_name") or "English"
	return {
		"language": language,
		"lang": language,
		"country": settings.country,
		"timezone": settings.time_zone,
		"currency": settings.currency,
		"enable_telemetry": settings.enable_telemetry,
	}


@frappe.whitelist()
def get_first_lead(name: str | None = None):
	# prefer the lead the user created during onboarding, if it still exists, is unconverted
	# and the user can still read it
	if name and frappe.get_list("CRM Lead", filters={"name": name, "converted": 0}, pluck="name", limit=1):
		return name

	lead = frappe.get_list(
		"CRM Lead",
		filters={"converted": 0},
		pluck="name",
		order_by="creation",
		limit=1,
	)
	return lead[0] if lead else None


@frappe.whitelist()
def get_first_deal(name: str | None = None):
	# prefer the deal the user created during onboarding, if it still exists and the user can still read it
	if name and frappe.get_list("CRM Deal", filters={"name": name}, pluck="name", limit=1):
		return name

	deal = frappe.get_list(
		"CRM Deal",
		pluck="name",
		order_by="creation",
		limit=1,
	)
	return deal[0] if deal else None
