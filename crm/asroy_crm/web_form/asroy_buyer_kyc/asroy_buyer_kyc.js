frappe.ready(function() {
	// bind events here
})

frappe.web_form.after_load = () => {
    frappe.web_form.set_df_property('locations', 'options', [
        'New York', 'London', 'Tokyo', 'Paris'
    ]);
};