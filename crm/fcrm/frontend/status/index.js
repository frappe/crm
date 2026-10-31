// The status control on CRM Lead's and CRM Deal's record pages: `header.status`, before Save.
import { listDocuments } from '@framework/ui/api'
import { __ } from 'frappe/i18n'
import StatusControl from './StatusControl.vue'
import { STATUS_DOCTYPES, STATUS_FIELDS, keepLostReason, placeStatusControl } from './statusChange.js'

export function addStatusControl(page) {
	placeStatusControl(page, StatusControl, readStatuses)
}

/** The `status` field handler: a Lost status picked in the form asks for its reason. */
export function askReasonForLostStatus(page) {
	return keepLostReason(page, readStatuses(STATUS_DOCTYPES[page.doctype]), __('Lost Reason'))
}

function readStatuses(doctype) {
	return listDocuments(doctype, { fields: STATUS_FIELDS, order_by: 'position asc', limit: 100 }).then(
		(reply) => reply.data,
	)
}
