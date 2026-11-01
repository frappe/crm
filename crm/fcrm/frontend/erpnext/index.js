// ERPNext's Create Quotation and View Customer entries on CRM Deal's record page, while the v1 row is enabled.
import { __ } from 'frappe/i18n'
import { standardScriptEnabled } from '../form_script/standardScript.js'
import { placeQuotationItems } from './quotation.js'

const LABELS = {
	get createQuotation() {
		return __('Create Quotation')
	},
	get viewCustomer() {
		return __('View Customer')
	},
	get quotationFailed() {
		return __('Error while creating quotation in ERPNext')
	},
}

export function addQuotationItems(page) {
	placeQuotationItems(page, LABELS, standardScriptEnabled)
}
