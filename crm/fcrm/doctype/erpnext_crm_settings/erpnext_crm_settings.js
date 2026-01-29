// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("ERPNext CRM Settings", {
  refresh(frm) {
    if (!frm.doc.enabled) return;
    frm.add_custom_button(__("Reset ERPNext form script"), () => {
      frappe.confirm(
        __(
          "Are you sure you want to reset 'Create Quotation from CRM Deal' form script?",
        ),
        () => frm.trigger("reset_erpnext_form_script"),
      );
    });
  },
  async reset_erpnext_form_script(frm) {
    let script = await frm.call("reset_erpnext_form_script");
    script.message && frappe.msgprint(__("Form script updated successfully"));
  },
});
