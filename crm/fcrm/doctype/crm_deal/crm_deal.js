// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("CRM Deal", {
	refresh(frm) {
		frm.add_web_link(`/crm/deals/${frm.doc.name}`, __("Open in Portal"));
		
		// add '%' sign for probability
		if (frm.doc.probability){
			$('[data-fieldname="probability"] input').val(frm.doc.probability + "%")
	    }

		frm.set_query('status_detail', () => {
			return {
				filters:[
					['crm_deal_status', '=', frm.doc.status],
					['active', '=', 1],
				]
			}
		})




	},
	probability(frm){
		// add '%' sign for probability
		if (frm.doc.probability) {
            $('[data-fieldname="probability"] input').val(frm.doc.probability + "%")
        }
	}
	
});
