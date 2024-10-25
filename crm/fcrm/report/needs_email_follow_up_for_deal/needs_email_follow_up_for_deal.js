// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Needs Email Follow Up For Deal"] = {
	"filters": [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.add_days(frappe.datetime.nowdate(), -7),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.nowdate()
		},
		{
			fieldname: "assigned_to",
			label: __("Assigned To"),
			fieldtype: "Link",
			options: "User",
		    default:frappe.session.user
		},
		{
			"fieldname": "status",
			"label": "Status",
            "fieldtype": "Link",
            "options": 	"CRM Deal Status"
		},
	],
	on_change: function() {
	    frappe.query_report.refresh();
	}
};
