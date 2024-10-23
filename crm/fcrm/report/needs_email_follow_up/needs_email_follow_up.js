// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Needs Email Follow Up"] = {
	"filters": [
		{
			"fieldname": "status",
			"label": "Lead Status",
            "fieldtype": "Link",
            "options": 	"CRM Lead Status"
		},
		{
			"fieldname": "assigned_to",
			"label": "Assigned To",
			"fieldtype": "Link",
			"options": "User",
			"default": frappe.session.user
		},
		{
			"fieldname": "n_days",
			"label": "Days Since Last Email",
			"fieldtype": "Int",
			"default": 7
		}
		
    ]
};
