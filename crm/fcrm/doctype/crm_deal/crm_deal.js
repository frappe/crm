// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("CRM Deal", {
	refresh(frm) {
		frm.add_web_link(`/crm/deals/${frm.doc.name}`, __("Open in Portal"));
	},
	update_total: function (frm) {
		let total = 0;
		let total_qty = 0;
		let net_total = 0;
		frm.doc.products.forEach((d) => {
			total += d.amount;
			total_qty += d.qty;
			net_total += d.net_amount;
		});

		frappe.model.set_value(frm.doctype, frm.docname, "total", total);
		frappe.model.set_value(
			frm.doctype,
			frm.docname,
			"net_total",
			net_total || total
		);
	}
});

frappe.ui.form.on("CRM Products", {
	products_add: function (frm, cdt, cdn) {
		frm.trigger("update_total");
	},
	products_remove: function (frm, cdt, cdn) {
		frm.trigger("update_total");
	},
	product_code: function (frm, cdt, cdn) {
		let d = frappe.get_doc(cdt, cdn);
		frappe.model.set_value(cdt, cdn, "product_name", d.product_code);
	},
	rate: function (frm, cdt, cdn) {
		let d = frappe.get_doc(cdt, cdn);
		if (d.rate && d.qty) {
			frappe.model.set_value(cdt, cdn, "amount", d.rate * d.qty);
		}
		frm.trigger("update_total");
	},
	qty: function (frm, cdt, cdn) {
		let d = frappe.get_doc(cdt, cdn);
		if (d.rate && d.qty) {
			frappe.model.set_value(cdt, cdn, "amount", d.rate * d.qty);
		}
		frm.trigger("update_total");
	},
	discount_percentage: function (frm, cdt, cdn) {
		let d = frappe.get_doc(cdt, cdn);
		if (d.discount_percentage && d.amount) {
			discount_amount = (d.discount_percentage / 100) * d.amount;
			frappe.model.set_value(
				cdt,
				cdn,
				"discount_amount",
				discount_amount
			);
			frappe.model.set_value(
				cdt,
				cdn,
				"net_amount",
				d.amount - discount_amount
			);
		}
		frm.trigger("update_total");
	}
});
