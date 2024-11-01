// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Deals Forecast"] = {
	"filters": [
		{
			"fieldname": "status",
			"label": "Status",
			"fieldtype": "Link",
			"options": "CRM Deal Status",
			"reqd": 0,
			get_query: function () {
				return {
					filters: [["name", "!=", "Closed"]]
				};
			}
		}
	]
};
