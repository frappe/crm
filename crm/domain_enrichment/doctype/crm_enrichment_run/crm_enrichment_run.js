// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

// CRM Enrichment Run is a read-only audit log -- it is never created by hand.
// Each run gets a "Retry" button that re-runs the enrichment for its linked
// Lead / Deal / Organization. A retry produces a NEW run row (the log is
// append-only), so on completion we point the user at the fresh run.

frappe.ui.form.on("CRM Enrichment Run", {
	refresh(frm) {
		if (frm.is_new()) return;
		if (!frm.doc.reference_doctype || !frm.doc.reference_name) return;

		frm.add_custom_button(__("Retry Enrichment"), () => {
			crm_enrichment_run_retry(frm);
		});
	},
});

function crm_enrichment_run_retry(frm) {
	const total = 7; // pipeline.PROGRESS_STEPS
	frappe.show_progress(__("Domain Enrichment"), 0, total, __("Queued…"));

	const event = "domain_enrichment_progress";
	const handler = (data) => {
		if (
			!data ||
			data.reference_doctype !== frm.doc.reference_doctype ||
			data.reference_name !== frm.doc.reference_name
		) {
			return; // not for this run's record
		}

		frappe.show_progress(__("Domain Enrichment"), data.step, data.total, data.message);

		if (data.status === "completed") {
			frappe.realtime.off(event, handler);
			frappe.hide_progress();
			frappe.show_alert(
				{ message: __("Enrichment complete — a new run was created"), indicator: "green" },
				7
			);
		} else if (data.status === "error") {
			frappe.realtime.off(event, handler);
			frappe.hide_progress();
			frappe.msgprint({
				title: __("Enrichment Failed"),
				message: data.message || __("See Error Log."),
				indicator: "red",
			});
		}
	};

	frappe.realtime.on(event, handler);

	frappe.call({
		method: "crm.domain_enrichment.api.retry",
		args: { run: frm.doc.name },
		error: () => {
			frappe.realtime.off(event, handler);
			frappe.hide_progress();
		},
	});
}
