// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("FCRM Settings", {
	// refresh(frm) {

	// },
	restore_defaults: function (frm) {
		let message = __(
			"This will restore (if not exist) all the default statuses, custom fields and layouts. Delete & Restore will delete default layouts and then restore them."
		);
		let d = new frappe.ui.Dialog({
			title: __("Restore Defaults"),
			primary_action_label: __("Restore"),
			primary_action: () => {
				frm.call("restore_defaults", { force: false }, () => {
					frappe.show_alert({
						message: __(
							"Default statuses, custom fields and layouts restored successfully."
						),
						indicator: "green",
					});
				});
				d.hide();
			},
			secondary_action_label: __("Delete & Restore"),
			secondary_action: () => {
				frm.call("restore_defaults", { force: true }, () => {
					frappe.show_alert({
						message: __(
							"Default statuses, custom fields and layouts restored successfully."
						),
						indicator: "green",
					});
				});
				d.hide();
			},
		});
		d.show();
		d.set_message(message);
	},
});
