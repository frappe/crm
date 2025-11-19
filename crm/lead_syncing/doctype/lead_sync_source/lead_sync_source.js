// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Lead Sync Source", {
	refresh(frm) {
        frm.add_custom_button(__('Sync Now'), () => {
            frm.call("sync_leads").then(() => {
                frappe.msgprint(__('Lead sync initiated.'));
            });
        });
	},
	// added a filter to show form only liked to pages
	facebook_page(frm) {
        frm.set_query("facebook_lead_form", function () {
            return {
                filters: {
                    "page": frm.doc.facebook_page 
                }
            };
        });
    },
});
