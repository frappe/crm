// ERPNext's Create Quotation and View Customer entries on CRM Deal's record page.
import { __ } from 'frappe/i18n'
import { placeQuotationItems } from './quotation.js'

export function addQuotationItems(page) {
	placeQuotationItems(page, {
		get createQuotation() {
			return __('Create Quotation')
		},
		get viewCustomer() {
			return __('View Customer')
		},
		get quotationFailed() {
			return __('Error while creating quotation in ERPNext')
		},
	})
}
