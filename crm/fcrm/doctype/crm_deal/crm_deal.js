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
            if (frm.doc.annual_revenue){
            	frm.set_value('weighted_amount', (frm.doc.annual_revenue * (frm.doc.probability/100)))
            	frm.set_df_property("weighted_amount", "read_only", 1);
            }
        }
	},
	annual_revenue(frm){
		if (frm.doc.annual_revenue && frm.doc.probability){
        	frm.set_value('weighted_amount', (frm.doc.annual_revenue * (frm.doc.probability/100)))
        	frm.set_df_property("weighted_amount", "read_only", 1);
        }
	}
});
