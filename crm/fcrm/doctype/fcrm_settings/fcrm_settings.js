// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("FCRM Settings", {
	refresh(frm) {
		if (
			(frappe.user.has_role("Sales Manager") ||
				frappe.user.has_role("System Manager")) &&
			frappe.boot.user.defaults.crm_demo_data_created !== "1"
		) {
			frm.set_df_property("restore_demo_data", "hidden", false);
		} else {
			frm.set_df_property("restore_demo_data", "hidden", true);
		}
	},
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
						indicator: "green"
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
						indicator: "green"
					});
				});
				d.hide();
			}
		});
		d.show();
		d.set_message(message);
	},

	restore_demo_data: function (frm) {
		let d = new frappe.ui.Dialog({
			title: __("Restore Demo Data"),
			primary_action_label: __("Restore"),
			primary_action: () => {
				frm.call("restore_demo_data", { force: false }, () => {
					frappe.show_alert({
						message: __("Demo data restored successfully."),
						indicator: "green"
					});
				});
				d.hide();
			}
		});
		d.show();
		d.set_message(
			__(
				"This will restore the demo data. Are you sure you want to continue?"
			)
		);
	}
});
