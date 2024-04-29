// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("CRM Lead", {
	refresh(frm) {
		frm.add_web_link(`/crm/leads/${frm.doc.name}`, __("Open in Portal"));
	},
});
