// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Opportunity", {
	refresh(frm) {
		frm.add_web_link(`/next-crm/opportunities/${frm.doc.name}`, __("Open in Portal"));
	},
});
