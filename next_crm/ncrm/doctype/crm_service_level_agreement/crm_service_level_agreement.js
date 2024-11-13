// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("CRM Service Level Agreement", {
	validate(frm) {
		let default_priority_count = 0;
		frm.doc.priorities.forEach(function (row) {
			if (row.default_priority) {
				default_priority_count++;
			}
		});
		if (default_priority_count > 1) {
			frappe.throw(
				__("There can only be one default priority in Priorities table")
			);
		}
	},
});
