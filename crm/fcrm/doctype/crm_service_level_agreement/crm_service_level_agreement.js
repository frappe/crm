// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

// frappe.ui.form.on("CRM Service Level Agreement", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("CRM Service Level Priority", {
	priorities_add: function (frm, cdt, cdn) {
		if (frm.doc.apply_on == "CRM Deal") {
			frappe.model.set_value(
				cdt,
				cdn,
				"reference_doctype",
				"CRM Deal Status"
			);
		}
	},
});
