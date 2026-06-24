import logging

import frappe


def complete_setup_for_fc_site(login_manager=None):
	"""Auto-complete the setup wizard on Frappe Cloud provisioned sites.

	When Press provisions a CRM trial site it prefills System Settings and creates
	the real System User via `initialize_system_settings_and_user`, but leaves
	`setup_complete` as 0 — which forces the user through the redundant desk setup
	wizard at `/app`. The data that wizard collects has already been gathered during
	Frappe Cloud signup, so we mark setup complete on first authenticated login.

	Runs from the `on_login` hook (see hooks.py): every user who reaches `/crm` must
	authenticate, so this is guaranteed to fire before they hit the wizard, on both
	fresh provisions and re-provisions. The `is_setup_complete()` guard makes it
	idempotent and cheap on subsequent logins.
	"""
	# Dedicated log file (logs/fc_onboarding.log) so the auto-complete decision path
	# can be traced on test deployments without sifting through the main web log.
	# Force INFO: frappe's default level is ERROR on non-dev benches (see
	# frappe/utils/logger.py default_log_level), which would silently drop every
	# line below and leave the file empty.
	logger = frappe.logger("fc_onboarding", allow_site=True, file_count=5)
	logger.setLevel(logging.INFO)

	# Snapshot the full decision state up front, so the log shows why we proceed or
	# bail regardless of which guard fires first.
	setup_complete = frappe.is_setup_complete()
	system_settings_setup_complete = frappe.db.get_single_value("System Settings", "setup_complete")
	non_admin_system_user_exists = bool(
		frappe.db.exists(
			"User",
			{"user_type": "System User", "name": ("not in", ("Administrator", "Guest"))},
		)
	)
	skip_setup_wizard = bool(frappe.conf.skip_setup_wizard)
	logger.info(
		"complete_setup_for_fc_site: invoked | "
		f"session.user={frappe.session.user} | "
		f"is_setup_complete()={setup_complete} | "
		f"System Settings.setup_complete={system_settings_setup_complete} | "
		f"non_admin_system_user_exists={non_admin_system_user_exists} | "
		f"skip_setup_wizard={skip_setup_wizard}"
	)

	# Act only while setup is pending, and only for a real System User. These cheap
	# guards run first so the common case (setup already complete) returns before
	# importing anything or hitting the DB.
	if setup_complete:
		logger.info("complete_setup_for_fc_site: bail — setup already complete")
		return
	# Site has opted out of the setup wizard entirely (site_config), so there is
	# nothing to auto-complete.
	if skip_setup_wizard:
		logger.info("complete_setup_for_fc_site: bail — skip_setup_wizard set in site_config")
		return

	# Only auto-complete once Frappe Cloud has prefilled the account — which it
	# signals by creating a real (non-Administrator) System User on the site. Until
	# then there is no gathered data to stand in for the wizard, so let it run.
	#
	# We check that such a user *exists*, not that the *logged-in* user is one:
	# while setup is pending, Press's "Setup Site" action logs in as Administrator
	# (POST /api/method/login), so gating on the session user would skip exactly the
	# login that lands on the wizard.
	if not non_admin_system_user_exists:
		logger.info("complete_setup_for_fc_site: bail — no prefilled non-admin System User yet")
		return

	# Imported lazily and guarded: on installs without the frappe_providers integration
	# (older versions / community forks) the module is absent, which also means the site
	# can't be a Frappe Cloud site — so bail out without letting the ImportError bubble
	# up and abort the login request.
	try:
		from frappe.integrations.frappe_providers.frappecloud_billing import is_fc_site
	except ImportError:
		logger.info("complete_setup_for_fc_site: bail — frappe_providers integration absent (not an FC site)")
		return

	if not is_fc_site():
		logger.info(
			"complete_setup_for_fc_site: bail — is_fc_site() is False (no System Manager role / no fc_communication_secret)"
		)
		return

	from frappe.desk.page.setup_wizard.setup_wizard import enable_setup_wizard_complete

	# Run CRM's `setup_wizard_complete` hook(s) (demo data). Enqueued so the seeding
	# work doesn't slow down or risk failing the login request — the flags below
	# flip synchronously so `setup_complete` is true immediately.
	for hook in frappe.get_hooks("setup_wizard_complete"):
		frappe.enqueue(hook, enqueue_after_commit=True)

	# Flip the completion flags. Marking "frappe" is enough for frappe.is_setup_complete()
	# (it only checks installed-app rows, so erpnext is irrelevant on a CRM-only site);
	# "crm" is marked too so the wizard doesn't re-prompt for CRM's stage.
	enable_setup_wizard_complete("frappe")
	enable_setup_wizard_complete("crm")
	frappe.db.set_single_value("System Settings", "setup_complete", 1)
	logger.info("complete_setup_for_fc_site: marked setup complete (frappe + crm + System Settings)")


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
