// ERPNext's entries on CRM Deal's record page, as CRM v1's "Create Quotation from CRM Deal" row adds them; free of the desk's imports so it is unit-tested.
const SETTINGS_METHODS = 'crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings'
export const QUOTATION_METHOD = `${SETTINGS_METHODS}.get_quotation_url`
export const CUSTOMER_METHOD = `${SETTINGS_METHODS}.get_customer_link`

/** Adds Create Quotation, and View Customer once the deal has one, to `⋯` while ERPNext CRM Settings is enabled. */
export function placeQuotationItems(page, labels) {
	if (page.isNew) return
	const enabled = page.cached('erpnext_enabled', () =>
		page.call('frappe.client.get_single_value', { doctype: 'ERPNext CRM Settings', field: 'enabled' }),
	)
	if (!enabled) return
	page.header.add({
		name: 'create_quotation',
		label: labels.createQuotation,
		icon: 'lucide-file-text',
		group: 'erpnext',
		run: (page) => openQuotation(page, labels.quotationFailed),
	})
	const customerUrl = page.cached(`erpnext_customer:${page.doc.erpnext_customer ?? ''}`, () =>
		page.call(CUSTOMER_METHOD, { crm_deal: page.docname }),
	)
	if (customerUrl)
		page.header.add({
			name: 'view_customer',
			label: labels.viewCustomer,
			icon: 'lucide-external-link',
			group: 'erpnext',
			run: () => window.open(customerUrl, '_blank'),
		})
}

/** Opens a new ERPNext quotation for the deal in a new tab; the host toasts a refused call. */
export async function openQuotation(page, failedMessage) {
	const url = await page.call(QUOTATION_METHOD, { crm_deal: page.docname, organization: page.doc.organization })
	if (url) window.open(url, '_blank')
	else page.toast.error(failedMessage)
}
