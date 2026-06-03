frappe.ui.form.on('Quotation', {
	refresh(frm) {
		const field = frm.get_field('crm_deal')
		if (!field) return
		field.df.formatter = (value) =>
			value
				? `<a href="/crm/deals/${encodeURIComponent(value)}" target="_blank" rel="noopener">${frappe.utils.escape_html(value)}</a>`
				: value
		field.refresh()
	},
	onload(frm) {
		const crm_deal = frm.doc.crm_deal || frappe.route_options?.crm_deal
		if (!crm_deal) return
		if ((frm.doc.items || []).some((i) => i.item_code)) return

		frappe.call({
			method: 'crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.prefill_quotation_items',
			args: { crm_deal },
			callback: async (r) => {
				if (!r.message || !r.message.length) return
				if (!frm.doc.price_list_currency && frm.doc.currency) {
					await frm.set_value('price_list_currency', frm.doc.currency)
				}
				frm.clear_table('items')
				for (const item of r.message) {
					const row = frm.add_child('items')
					await frappe.model.set_value(row.doctype, row.name, 'item_code', item.item_code)
					await frappe.model.set_value(row.doctype, row.name, 'qty', item.qty)
					// price_list_rate must be set before discount_percentage: ERPNext
					// resets the discount to 0 when price_list_rate is falsy.
					await frappe.model.set_value(row.doctype, row.name, 'price_list_rate', item.price_list_rate)
					await frappe.model.set_value(row.doctype, row.name, 'discount_percentage', item.discount_percentage)
				}
				frm.refresh_field('items')
			},
		})
	},
})
