// Copyright (c) 2024, Korecent and contributors
// For license information, please see license.txt

frappe.query_reports["Uncontacted Deals"] = {
	"filters":[
		{
			"fieldname": "user",
			"label": "Assigned To",
			"fieldtype": "Link",
			"options": "User",
			"default": frappe.session.user, 
			"reqd": 0
		},
		{
			"fieldname": "organization",
			"label": "Organization",
			"fieldtype": "Link",
			"options": "CRM Organization",
			"reqd": 0
		}
	]
};
