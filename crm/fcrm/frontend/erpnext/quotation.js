// ERPNext's entries on CRM Deal's record page, as CRM v1's "Create Quotation from CRM Deal" row adds them; free of the desk's imports so it is unit-tested.
const SETTINGS_METHODS = 'crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings'
export const QUOTATION_METHOD = `${SETTINGS_METHODS}.get_quotation_url`
export const CUSTOMER_METHOD = `${SETTINGS_METHODS}.get_customer_link`
export const QUOTATION_SCRIPT = 'Create Quotation from CRM Deal'

/** Adds Create Quotation, and View Customer once the deal has one, to `⋯` while ERPNext CRM Settings and the v1 row are enabled. */
export function placeQuotationItems(page, labels, scriptEnabled) {
	if (page.isNew) return
	const erpnext = page.cached(`erpnext:${page.doc.erpnext_customer ?? ''}`, () => readERPNext(page, scriptEnabled))
	if (!erpnext) return
	page.header.add({
		name: 'create_quotation',
		label: labels.createQuotation,
		icon: 'lucide-file-text',
		group: 'erpnext',
		run: (page) => openQuotation(page, labels.quotationFailed),
	})
	if (erpnext.customerUrl)
		page.header.add({
			name: 'view_customer',
			label: labels.viewCustomer,
			icon: 'lucide-external-link',
			group: 'erpnext',
			run: () => window.open(erpnext.customerUrl, '_blank'),
		})
}

/** The deal's customer link while ERPNext CRM Settings and the v1 row are enabled, else `null`; one key, so one replay fetches every read. */
async function readERPNext(page, scriptEnabled) {
	const enabled = await page.call('frappe.client.get_single_value', { doctype: 'ERPNext CRM Settings', field: 'enabled' })
	if (!enabled || !(await scriptEnabled(QUOTATION_SCRIPT))) return null
	// A failed customer lookup still leaves Create Quotation.
	const customerUrl = await page.call(CUSTOMER_METHOD, { crm_deal: page.docname }).catch(() => '')
	return { customerUrl }
}

/** Opens a new ERPNext quotation for the deal in a new tab, or toasts why it cannot. */
export async function openQuotation(page, failedMessage) {
	let url
	try {
		url = await page.call(QUOTATION_METHOD, { crm_deal: page.docname, organization: page.doc.organization })
	} catch (error) {
		// A throw out of the act makes the host reload over the reader's unsaved edits.
		return page.toast.error(error?.message || failedMessage)
	}
	if (url) window.open(url, '_blank')
	else page.toast.error(failedMessage)
}
