// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("CRM Yeastar Settings", {
  refresh(frm) {
    getToken(frm);
  },
});
function getToken(frm) {
  if (frm.is_new()) return;
  frm.add_custom_button(__("Get Token"), () => fetchToken(frm));
}

function fetchToken(frm) {
  frm.call({
    method: "generate_access_token",
    doc: frm.doc,
    freeze: true,
    freeze_message: "Fetching auth Token",
    callback: (r) => {
      frm.reload_doc();
      frappe.show_alert({
        message: __("Token retrieved successfully."),
        indicator: "green",
      });
    },
  });
}
