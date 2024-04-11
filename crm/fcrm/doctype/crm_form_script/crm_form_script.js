// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("CRM Form Script", {
	refresh(frm) {
		frm.set_query("dt", {
			filters: {
				istable: 0,
			},
		});
	},
	view(frm) {
		let has_form_boilerplate = frm.doc.script.includes(
			"function setupForm("
		);
		let has_list_boilerplate = frm.doc.script.includes(
			"function setupList("
		);

		if (frm.doc.view == "Form" && !has_form_boilerplate) {
			frm.doc.script = `
function setupForm({ doc }) {
	return {
		actions: [],
	}
}`.trim();
		}
		if (frm.doc.view == "List" && !has_list_boilerplate) {
			frm.doc.script = `
function setupList({ list }) {
	return {
		actions: [],
		bulk_actions: [],
	}
}`.trim();
		}
	},
});
