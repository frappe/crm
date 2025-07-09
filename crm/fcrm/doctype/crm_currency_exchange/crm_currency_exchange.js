// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("CRM Currency Exchange", {
	refresh(frm) {
		frm.add_custom_button(__("Update exchange rate"), () => {
			frm.trigger("update_exchange_rate");
		});
	},
	async update_exchange_rate(frm) {
		let r = await frm.call("update_exchange_rate");
		r.message && frappe.msgprint(__("Exchange rate updated successfully"));
	}
});
