// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Lead Sync Source", {
  refresh(frm) {
    frm.add_custom_button(__("Sync Now"), () => {
      frm.call("sync_leads").then(() => {
        frappe.msgprint(__("Lead sync initiated."));
      });
    });
  },
});
