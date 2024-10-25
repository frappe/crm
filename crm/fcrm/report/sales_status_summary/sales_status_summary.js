// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Status Summary"] = {
	"filters":[
        {
            "fieldname": "deal_owner",
            "label": "Deal Owner",
            "fieldtype": "Link",
            "options": "User",
            "reqd": 0
        },
        {
            "fieldname": "from_date",
            "label": "From Date",
            "fieldtype": "Date",
            "reqd": 0
		},
        {
            "fieldname": "to_date",
            "label": "To Date",
            "fieldtype": "Date",
            "reqd": 0        
		},
        {
            "fieldname": "crm_organization",
            "label": "CRM Organization",
            "fieldtype": "Link",
            "options": "CRM Organization",
            "reqd": 0
        },
        {
            "fieldname": "status",
            "label": "Deal Status",
            "fieldtype": "Link",
            "options": "CRM Deal Status",
            "reqd": 0
        }
    ]
};
