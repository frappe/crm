// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("CRM Holiday List", {
  clear_table(frm) {
    frm.set_value("holidays", []);
    frm.refresh_field("holidays");
    frm.dirty();
  },
  add_to_holidays(frm) {
    frm.call("get_weekly_off_dates").then((r) => {
      if (r && r.doc && r.doc.holidays) {
        frm.doc.holidays = r.doc.holidays;
      }
      frm.refresh_field("holidays");
      frm.dirty();
    });
  },
});
