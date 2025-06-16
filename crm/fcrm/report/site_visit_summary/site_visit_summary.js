// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Site Visit Summary"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "width": "80px"
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "width": "80px"
        },
        {
            "fieldname": "sales_person",
            "label": __("Sales Person"),
            "fieldtype": "Link",
            "options": "User",
            "width": "100px"
        },
        {
            "fieldname": "status",
            "label": __("Status"),
            "fieldtype": "Select",
            "options": "\nPlanned\nIn Progress\nCompleted\nCancelled\nPostponed",
            "width": "100px"
        },
        {
            "fieldname": "visit_type",
            "label": __("Visit Type"),
            "fieldtype": "Select",
            "options": "\nInitial Meeting\nDemo/Presentation\nNegotiation\nContract Signing\nFollow-up\nSupport\nOther",
            "width": "120px"
        },
        {
            "fieldname": "lead_quality",
            "label": __("Lead Quality"),
            "fieldtype": "Select",
            "options": "\nHot\nWarm\nCold\nNot Qualified",
            "width": "100px"
        }
    ],
    
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname == "status") {
            if (value == "Completed") {
                value = `<span class="indicator green">${value}</span>`;
            } else if (value == "In Progress") {
                value = `<span class="indicator blue">${value}</span>`;
            } else if (value == "Planned") {
                value = `<span class="indicator orange">${value}</span>`;
            } else if (value == "Cancelled") {
                value = `<span class="indicator red">${value}</span>`;
            }
        }
        
        if (column.fieldname == "lead_quality") {
            if (value == "Hot") {
                value = `<span class="indicator red">${value}</span>`;
            } else if (value == "Warm") {
                value = `<span class="indicator orange">${value}</span>`;
            } else if (value == "Cold") {
                value = `<span class="indicator blue">${value}</span>`;
            }
        }
        
        return value;
    },
    
    "onload": function(report) {
        // Add custom buttons
        report.page.add_inner_button(__("Export to Excel"), function() {
            frappe.utils.csvify(report.data, null, report.get_visible_columns());
        });
        
        report.page.add_inner_button(__("Create Site Visit"), function() {
            frappe.new_doc("CRM Site Visit");
        });
    }
};
