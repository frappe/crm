// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Uncontacted Leads"] = {
	"filters":[
		{
			"fieldname": "user",
			"label": "Assigned To",
			"fieldtype": "Link",
			"options": "User",
			"default": frappe.session.user,
			"reqd": 1
		}
	]
};
