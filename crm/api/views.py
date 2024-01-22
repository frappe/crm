import frappe
from pypika import Criterion


@frappe.whitelist()
def get_views(doctype, is_view=False):
	if frappe.session.user == "Guest":
		frappe.throw("Authentication failed", exc=frappe.AuthenticationError)

	View = frappe.qb.DocType("CRM View Settings")
	query = (
		frappe.qb.from_(View)
		.select("*")
		.where(Criterion.any([View.user == '', View.user == frappe.session.user]))
	)
	if is_view:
		query = query.where(View.is_view == True)
	if doctype:
		query = query.where(View.dt == doctype)
	views = query.run(as_dict=True)
	return views