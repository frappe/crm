import frappe


def create_demo_leads(demo_users):
	# first lead owned by the logged-in user (personal feel)
	# rest distributed across demo users
	session_user = frappe.session.user
	owner_1 = demo_users[0] if len(demo_users) > 0 else session_user
	owner_2 = demo_users[1] if len(demo_users) > 1 else session_user

	leads_data = [
		{
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
			"lead_owner": session_user,
		},
		{
			"first_name": "Bob",
			"last_name": "Martinez",
			"email": "bob.martinez@example.com",
			"mobile_no": "+1 555 000 5678",
			"organization": "Globex Industries",
			"job_title": "CEO",
			"status": "Contacted",
			"source": "Advertisement",
			"no_of_employees": "51-200",
			"annual_revenue": 8000000,
			"lead_owner": owner_1,
		},
		{
			"first_name": "Carol",
			"last_name": "Smith",
			"email": "carol.smith@example.com",
			"mobile_no": "+1 555 000 9012",
			"organization": "BrightPath Ltd",
			"job_title": "Head of Operations",
			"status": "Nurture",
			"source": "Email",
			"no_of_employees": "11-50",
			"annual_revenue": 1500000,
			"lead_owner": owner_2,
		},
		{
			"first_name": "David",
			"last_name": "Lee",
			"email": "david.lee@example.com",
			"mobile_no": "+1 555 000 3456",
			"organization": "TechStart Inc",
			"job_title": "CTO",
			"status": "Qualified",
			"source": "Reference",
			"no_of_employees": "1-10",
			"annual_revenue": 500000,
			"lead_owner": owner_1,
		},
	]

	created = []
	for data in leads_data:
		lead = frappe.get_doc({"doctype": "CRM Lead", **data}).insert(ignore_permissions=True)
		created.append(lead.name)

	return created


def delete_demo_leads(lead_names):
	for name in lead_names:
		if frappe.db.exists("CRM Lead", name):
			frappe.delete_doc("CRM Lead", name, ignore_permissions=True, force=True)
