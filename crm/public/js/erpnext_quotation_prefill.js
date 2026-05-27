frappe.ui.form.on('Quotation', {
	onload(frm) {
		const crm_deal = frm.doc.crm_deal || frappe.route_options?.crm_deal
		if (!crm_deal) return
		if ((frm.doc.items || []).some((i) => i.item_code)) return

		frappe.call({
			method: 'crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.prefill_quotation_items',
			args: { crm_deal },
			callback: async (r) => {
				if (!r.message || !r.message.length) return
				frm.clear_table('items')
				for (const item of r.message) {
					const row = frm.add_child('items')
					await frappe.model.set_value(row.doctype, row.name, 'item_code', item.item_code)
					await frappe.model.set_value(row.doctype, row.name, 'qty', item.qty)
					await frappe.model.set_value(row.doctype, row.name, 'rate', item.rate)
				}
				frm.refresh_field('items')
			},
		})
	},
})
