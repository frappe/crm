// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("CRM Service Level Agreement", {
	// refresh(frm) {},

	apply_sla_for_follow_up: function (frm) {
		frm.trigger("toggle_follow_up_fields");
	},

	toggle_follow_up_fields: function (frm) {
		if (cint(frm.doc.apply_sla_for_follow_up) === 1) {
			frm.fields_dict.priorities.grid.update_docfield_property(
				"follow_up_time",
				"hidden",
				0
			);
			frm.fields_dict.priorities.grid.update_docfield_property(
				"follow_up_time",
				"reqd",
				1
			);
		} else {
			frm.fields_dict.priorities.grid.update_docfield_property(
				"follow_up_time",
				"hidden",
				1
			);
			frm.fields_dict.priorities.grid.update_docfield_property(
				"follow_up_time",
				"reqd",
				0
			);
		}

		frm.refresh_field("priorities");
	},
});
