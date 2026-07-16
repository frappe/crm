// Domain Enrichment — desk form button + live progress.
//
// Adds an "Enrich from Website" button to CRM Lead / CRM Organization / CRM Deal.
// Clicking it queues a background job; the progress steps stream back over realtime
// and are shown to the user. When done, the form reloads to show the enriched fields.

frappe.provide("crm.domain_enrichment");

crm.domain_enrichment.setup = function (frm) {
	if (frm.is_new()) return;

	frm.add_custom_button(__("Enrich from Website"), () => {
		const website = (frm.doc.website || "").trim();
		if (!website) {
			frappe.msgprint({
				title: __("No Website"),
				message: __("Set a Website on this record before enriching."),
				indicator: "orange",
			});
			return;
		}
		crm.domain_enrichment.run(frm, website);
	});
};

crm.domain_enrichment.run = function (frm, website) {
	// A determinate progress dialog driven by realtime events.
	const total = 7; // pipeline.PROGRESS_STEPS; each event also carries data.total
	frappe.show_progress(__("Domain Enrichment"), 0, total, __("Queued…"));

	const event = "domain_enrichment_progress";
	const handler = (data) => {
		if (
			!data ||
			data.reference_doctype !== frm.doctype ||
			data.reference_name !== frm.docname
		) {
			return; // not for this document
		}

		frappe.show_progress(
			__("Domain Enrichment"),
			data.step,
			data.total,
			data.message
		);

		if (data.status === "completed") {
			frappe.realtime.off(event, handler);
			frappe.hide_progress();
			frappe.show_alert(
				{ message: __("Enrichment complete"), indicator: "green" },
				5
			);
			frm.reload_doc();
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
		method: "crm.domain_enrichment.api.enrich",
		args: {
			reference_doctype: frm.doctype,
			reference_name: frm.docname,
		},
		error: () => {
			frappe.realtime.off(event, handler);
			frappe.hide_progress();
		},
	});
};

["CRM Lead", "CRM Organization", "CRM Deal"].forEach((doctype) => {
	frappe.ui.form.on(doctype, {
		refresh: crm.domain_enrichment.setup,
	});
});
