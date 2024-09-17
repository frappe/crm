// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("ERPNext CRM Settings", {
	refresh(frm) {
		if (!frm.doc.enabled) return;
		frm.add_custom_button(__("Reset ERPNext Form Script"), () => {
			frappe.confirm(
				__(
					"Are you sure you want to reset 'Create Quotation from CRM Deal' Form Script?"
				),
				() => frm.trigger("update_form_script")
			);
		});
	},
	async update_form_script() {
		let script = await frappe.call(
			"crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.get_crm_form_script"
		);
		if (script.message) {
			let form_script = await frappe.db.set_value(
				"CRM Form Script",
				"Create Quotation from CRM Deal",
				"script",
				script.message
			);
			if (form_script.message) {
				frappe.msgprint(__("Form Script updated successfully"));
			}
		}
	},
});
