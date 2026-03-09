// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("CRM Product", {
  product_code: function (frm) {
    if (!frm.doc.product_name)
      frm.set_value("product_name", frm.doc.product_code);
  },
});
