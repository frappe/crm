frappe.ui.form.on("CRM Task", {
	onload: function (frm) {
		frm.set_query("reference_doctype", function () {
			return {
				filters: {
					name: ["in", ["Asroy Seller Lead", "Asroy Buyer Lead","CRM Lead"]],
				},
			};
		});
	},
});
