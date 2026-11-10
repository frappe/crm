import frappe
from typing import Any


@frappe.whitelist()
def get_organization_tab_counts() -> dict[str, Any]:
	"""Dynamic counts for All, Active, and Inactive organization tabs."""
	user = frappe.session.user
	from crm.api.security import is_admin_only, get_organization_permission_conditions

	is_admin = is_admin_only(user)

	if is_admin:
		all_count = frappe.db.count("CRM Organization")
		active_count = frappe.db.sql("""
			SELECT COUNT(*) FROM `tabCRM Organization`
			WHERE status = 'Active' OR status IS NULL OR status = ''
		""")[0][0]
		inactive_count = frappe.db.sql("""
			SELECT COUNT(*) FROM `tabCRM Organization`
			WHERE status = 'Inactive'
		""")[0][0]
	else:
		cond = get_organization_permission_conditions(user)
		base_where = f"WHERE ({cond})" if cond else ""
		all_count = frappe.db.sql(f"SELECT COUNT(*) FROM `tabCRM Organization` {base_where}")[0][0]

		active_where = (
			f"WHERE ({cond}) AND (status = 'Active' OR status IS NULL OR status = '')"
			if cond
			else "WHERE (status = 'Active' OR status IS NULL OR status = '')"
		)
		active_count = frappe.db.sql(f"SELECT COUNT(*) FROM `tabCRM Organization` {active_where}")[0][0]

		inactive_where = f"WHERE ({cond}) AND status = 'Inactive'" if cond else "WHERE status = 'Inactive'"
		inactive_count = frappe.db.sql(f"SELECT COUNT(*) FROM `tabCRM Organization` {inactive_where}")[0][0]

	return {
		"all": all_count,
		"active": active_count,
		"inactive": inactive_count,
	}


@frappe.whitelist()
def update_organization_status(organization: str, status: str) -> dict[str, Any]:
	"""Update status of a CRM Organization to Active or Inactive."""
	if status not in ("Active", "Inactive"):
		frappe.throw(frappe._("Status must be either Active or Inactive"))

	doc = frappe.get_doc("CRM Organization", organization)
	doc.status = status
	doc.save()
	return {"name": doc.name, "status": doc.status}
