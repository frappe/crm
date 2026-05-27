frappe.listview_settings["CRM Product"] = {
  onload(listview) {
    listview.page.set_primary_action(__("Add CRM Product"), async () => {
      const enabled = await frappe.db.get_single_value(
        "ERPNext CRM Settings",
        "enabled",
      );
      if (enabled) {
        frappe.show_alert({
          message: __("Create products as Items in ERPNext"),
          indicator: "blue",
        });
        frappe.set_route("Form", "Item", "new");
      } else {
        frappe.new_doc("CRM Product");
      }
    });
  },
};
