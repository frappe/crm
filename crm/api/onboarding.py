import frappe


def complete_setup_for_fc_site(doc, method=None):
	"""Auto-complete the setup wizard on Frappe Cloud provisioned sites.

	When Press provisions a CRM trial site it prefills System Settings and creates
	the real System User via `initialize_system_settings_and_user`, but leaves
	`setup_complete` as 0 — which forces the user through the redundant desk setup
	wizard at `/app`. The data that wizard collects has already been gathered during
	Frappe Cloud signup, so we mark setup complete the moment that user is inserted.

	This fires from `User.after_insert` (see `doc_events` in hooks.py). The prefill's
	`create_or_update_user()` is the last step it runs, so by the time this handler
	executes both System Settings and the user already exist.
	"""
	# Only act during the provisioning window, for the prefilled System User. These
	# cheap guards run first so the common case (setup already complete) returns before
	# importing anything.
	if frappe.is_setup_complete():
		return
	if doc.user_type != "System User" or doc.name == "Administrator":
		return

	# Imported lazily and guarded: on installs without the frappe_providers integration
	# (older versions / community forks) the module is absent, which also means the site
	# can't be a Frappe Cloud site — so bail out without letting the ImportError bubble
	# up and abort the in-progress user-insert transaction.
	try:
		from frappe.integrations.frappe_providers.frappecloud_billing import is_fc_site
	except ImportError:
		return

	if not is_fc_site():
		return

	from frappe.desk.page.setup_wizard.setup_wizard import enable_setup_wizard_complete

	# Run CRM's `setup_wizard_complete` hook(s) (demo data). Enqueued so the seeding
	# work doesn't slow down or risk failing Press's prefill request — the flags below
	# flip synchronously so `setup_complete` is true immediately.
	for hook in frappe.get_hooks("setup_wizard_complete"):
		frappe.enqueue(hook, enqueue_after_commit=True)

	# Flip the completion flags. Marking "frappe" is enough for frappe.is_setup_complete()
	# (it only checks installed-app rows, so erpnext is irrelevant on a CRM-only site);
	# "crm" is marked too so the wizard doesn't re-prompt for CRM's stage.
	enable_setup_wizard_complete("frappe")
	enable_setup_wizard_complete("crm")
	frappe.db.set_single_value("System Settings", "setup_complete", 1)


def set_home_page_on_login(login_manager=None):
	"""Land users on the CRM app only when it is the sole product app installed.

	Frappe routes System Users to the desk after login (via `get_home_page()`), which
	doesn't consult the app-screen logic that already knows the default app. So on a
	CRM-only site we set the request-scoped `home_page` flag — which `get_home_page()`
	honours first — to send users to `/crm`. On a multi-app site we leave it unset so
	users fall through to the desk, matching Frappe's `get_default_path()` behaviour.
	"""
	from frappe.apps import get_apps

	product_apps = [app for app in get_apps() if app.get("name") != "frappe"]
	if len(product_apps) == 1 and product_apps[0].get("name") == "crm":
		frappe.local.flags.home_page = "crm"


@frappe.whitelist()
def get_first_lead():
	lead = frappe.get_all(
		"CRM Lead",
		filters={"converted": 0},
		fields=["name"],
		order_by="creation",
		limit=1,
	)
	return lead[0].name if lead else None


@frappe.whitelist()
def get_first_deal():
	deal = frappe.get_all(
		"CRM Deal",
		fields=["name"],
		order_by="creation",
		limit=1,
	)
	return deal[0].name if deal else None
