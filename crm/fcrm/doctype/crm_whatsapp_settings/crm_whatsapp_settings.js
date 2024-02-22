// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("CRM Whatsapp Settings", {
	refresh(frm) {
		// add send whatsapp message button
		frm.add_custom_button(__("Send Message"), () => {
			frappe.call("crm.integrations.whatsapp.api.send_message", {
				data: "",
				to: "917666980887",
			});
		});
	},
});
