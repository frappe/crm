import frappe

from crm.utils import sales_user_only

LANDING_PAGE_KEY = "crm_landing_page"


@frappe.whitelist(methods=["POST"])
@sales_user_only
def set_landing_page(page: str | None = None):
	"""Store where `/` sends the user: Home (cleared), a page route name or a CRM View Settings name."""
	if not page or page == "Home":
		frappe.defaults.clear_user_default(LANDING_PAGE_KEY)
	else:
		frappe.defaults.set_user_default(LANDING_PAGE_KEY, page)
