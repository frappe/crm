import frappe


def create_demo_leads():
	lead = frappe.get_doc(
		{
			"doctype": "CRM Lead",
			"first_name": "Alice",
			"last_name": "Johnson",
			"email": "alice.johnson@example.com",
			"mobile_no": "+1 555 000 1234",
			"organization": "Acme Corp",
			"job_title": "VP of Engineering",
			"status": "New",
			"source": "Cold Calling",
			"no_of_employees": "201-500",
			"annual_revenue": 5000000,
		}
	).insert(ignore_permissions=True)

	return [lead.name]


def delete_demo_leads(names):
	for name in names:
		if frappe.db.exists("CRM Lead", name):
			frappe.delete_doc("CRM Lead", name, ignore_permissions=True, force=True)
