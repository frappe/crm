// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Failed Lead Sync Log", {
  refresh(frm) {
    const btn = frm.add_custom_button(__("Retry sync"), () => {
      frm
        .call({
          doc: frm.doc,
          method: "retry_sync",
          btn,
        })
        .then(({ message }) => {
          frappe.show_alert(
            __("Sync successful, CRM Lead: {0}!", [
              frappe.utils.get_form_link("CRM Lead", message.name, true),
            ]),
          );
        });
    });
  },
});
