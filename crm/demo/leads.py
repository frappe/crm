from datetime import datetime, timedelta

import frappe

from crm.demo.utils import backdate, fix_auto_records, resolve_owners

# Days ago each lead was created — index matches leads_data order
_LEAD_DAYS = [58, 52, 47, 43, 38, 34, 28, 22, 17, 30, 13, 8]

# Last-activity date per lead (used for modified so active leads sort to top).
# Converted leads will be overwritten by create_demo_deals anyway.
# Index: [0]alice [1]bob [2]carol [3]david [4]eve [5]frank [6]grace [7]henry [8]iris [9]jack [10]karen [11]leo
_LEAD_LAST_TOUCHED_DAYS = [50, 8, 11, 37, 38, 34, 28, 18, 11, 24, 9, 5]


def create_demo_leads(demo_users):
	session_user, owner_1, owner_2, owner_3 = resolve_owners(demo_users)

	leads_data = [
		# [0] Alice — will be converted to a deal
		{
			"first_name": "Alice",
			"last_name": "Johnson",
			"email": "alice.johnson@example.com",
			"mobile_no": "+1 555 000 1234",
			"organization": "Acme Corp",
			"website": "https://acmecorp.example.com",
			"industry": "Technology",
			"job_title": "VP of Engineering",
			"status": "Qualified",
			"source": "Cold Calling",
			"no_of_employees": "201-500",
			"annual_revenue": 5000000,
			"lead_owner": session_user,
		},
		# [1] Bob — stays as a lead
		{
			"first_name": "Bob",
			"last_name": "Martinez",
			"email": "bob.martinez@example.com",
			"mobile_no": "+1 555 000 5678",
			"organization": "Globex Industries",
			"website": "https://globexindustries.example.com",
			"industry": "Manufacturing",
			"job_title": "CEO",
			"status": "Contacted",
			"source": "Advertisement",
			"no_of_employees": "51-200",
			"annual_revenue": 8000000,
			"lead_owner": owner_1,
		},
		# [2] Carol — stays as a lead
		{
			"first_name": "Carol",
			"last_name": "Smith",
			"email": "carol.smith@example.com",
			"mobile_no": "+1 555 000 9012",
			"organization": "BrightPath Ltd",
			"website": "https://brightpath.example.com",
			"industry": "Consulting",
			"job_title": "Head of Operations",
			"status": "Nurture",
			"source": "Email",
			"no_of_employees": "11-50",
			"annual_revenue": 1500000,
			"lead_owner": owner_2,
		},
		# [3] David — will be converted to a deal
		{
			"first_name": "David",
			"last_name": "Lee",
			"email": "david.lee@example.com",
			"mobile_no": "+1 555 000 3456",
			"organization": "TechStart Inc",
			"website": "https://techstart.example.com",
			"industry": "Technology",
			"job_title": "CTO",
			"status": "Qualified",
			"source": "Reference",
			"no_of_employees": "1-10",
			"annual_revenue": 500000,
			"lead_owner": owner_1,
		},
		# [4] Emma — stays as a lead
		{
			"first_name": "Emma",
			"last_name": "Williams",
			"email": "emma.williams@example.com",
			"mobile_no": "+1 555 000 2345",
			"organization": "CloudBase LLC",
			"website": "https://cloudbase.example.com",
			"industry": "Technology",
			"job_title": "Procurement Manager",
			"status": "New",
			"source": "Website",
			"no_of_employees": "51-200",
			"annual_revenue": 3000000,
			"lead_owner": owner_1,
		},
		# [5] Frank — stays as a lead
		{
			"first_name": "Frank",
			"last_name": "Turner",
			"email": "frank.turner@example.com",
			"mobile_no": "+1 555 000 6789",
			"organization": "DataSync Co",
			"website": "https://datasync.example.com",
			"industry": "Technology",
			"job_title": "Head of Sales",
			"status": "Nurture",
			"source": "Email",
			"no_of_employees": "11-50",
			"annual_revenue": 2000000,
			"lead_owner": owner_2,
		},
		# [6] Grace — stays as a lead
		{
			"first_name": "Grace",
			"last_name": "Park",
			"email": "grace.park@example.com",
			"mobile_no": "+1 555 000 0123",
			"organization": "NextWave Corp",
			"website": "https://nextwavecorp.example.com",
			"industry": "Telecommunications",
			"job_title": "COO",
			"status": "Contacted",
			"source": "Reference",
			"no_of_employees": "201-500",
			"annual_revenue": 12000000,
			"lead_owner": session_user,
		},
		# [7] Henry — will be converted to a deal
		{
			"first_name": "Henry",
			"last_name": "Adams",
			"email": "henry.adams@example.com",
			"mobile_no": "+1 555 000 4567",
			"organization": "PivotTech Solutions",
			"website": "https://pivottech.example.com",
			"industry": "Technology",
			"job_title": "CFO",
			"status": "Qualified",
			"source": "Advertisement",
			"no_of_employees": "51-200",
			"annual_revenue": 6000000,
			"lead_owner": owner_3,
		},
		# [8] Iris — will be converted to a deal
		{
			"first_name": "Iris",
			"last_name": "Chen",
			"email": "iris.chen@example.com",
			"mobile_no": "+1 555 000 7890",
			"organization": "ScaleUp Labs",
			"website": "https://scaleuplabs.example.com",
			"industry": "Technology",
			"job_title": "VP Engineering",
			"status": "Qualified",
			"source": "Cold Calling",
			"no_of_employees": "1-10",
			"annual_revenue": 750000,
			"lead_owner": session_user,
		},
		# [9] Jack — will be converted to a deal
		{
			"first_name": "Jack",
			"last_name": "Morrison",
			"email": "jack.morrison@example.com",
			"mobile_no": "+1 555 000 8901",
			"organization": "Meridian Systems",
			"website": "https://meridiansystems.example.com",
			"industry": "Defense",
			"job_title": "CEO",
			"status": "Qualified",
			"source": "Reference",
			"no_of_employees": "501-1000",
			"annual_revenue": 25000000,
			"lead_owner": owner_1,
		},
		# [10] Karen — will be converted to a Lost deal
		{
			"first_name": "Karen",
			"last_name": "White",
			"email": "karen.white@example.com",
			"mobile_no": "+1 555 000 2222",
			"organization": "Vertex Analytics",
			"website": "https://vertexanalytics.example.com",
			"industry": "Financial Services",
			"job_title": "Director of Strategy",
			"status": "Qualified",
			"source": "Advertisement",
			"no_of_employees": "201-500",
			"annual_revenue": 9000000,
			"lead_owner": owner_2,
		},
		# [11] Leo — will be converted to a Lost deal
		{
			"first_name": "Leo",
			"last_name": "Brown",
			"email": "leo.brown@example.com",
			"mobile_no": "+1 555 000 3333",
			"organization": "Forge Digital",
			"website": "https://forgedigital.example.com",
			"industry": "Advertising",
			"job_title": "Head of Product",
			"status": "Qualified",
			"source": "Cold Calling",
			"no_of_employees": "51-200",
			"annual_revenue": 4000000,
			"lead_owner": session_user,
		},
	]

	now = datetime.now()
	created = []
	for data, days in zip(leads_data, _LEAD_DAYS, strict=False):
		ts = now - timedelta(days=days)
		owner = data["lead_owner"]
		lead = frappe.get_doc({"doctype": "CRM Lead", **data}).insert(ignore_permissions=True)
		backdate("CRM Lead", lead.name, owner, ts)
		fix_auto_records("CRM Lead", lead.name, owner, ts)
		created.append(lead.name)

	return created


def rebackdate_demo_leads(lead_names, demo_users):
	"""Re-apply modified timestamps after activity creation resets them."""
	session_user, owner_1, owner_2, owner_3 = resolve_owners(demo_users)
	# Must match the lead_owner assignments in create_demo_leads (same index order)
	_owners = [
		session_user,
		owner_1,
		owner_2,
		owner_1,
		owner_1,
		owner_2,
		session_user,
		owner_3,
		session_user,
		owner_1,
		owner_2,
		session_user,
	]
	now = datetime.now()
	for name, days, owner in zip(lead_names, _LEAD_LAST_TOUCHED_DAYS, _owners, strict=False):
		backdate("CRM Lead", name, owner, now - timedelta(days=days), set_creation=False)


def delete_demo_leads(lead_names):
	for name in lead_names:
		if frappe.db.exists("CRM Lead", name):
			frappe.delete_doc("CRM Lead", name, ignore_permissions=True, force=True)
