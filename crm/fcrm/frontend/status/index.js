// Status on CRM Lead's and CRM Deal's record pages: the `header.status` control and the `status` field handler.
import { listDocuments } from '@framework/ui/api'
import { lostReasonLabels } from './lostReasonLabels.js'
import StatusControl from './StatusControl.vue'
import {
	STATUS_DOCTYPES,
	STATUS_FIELDS,
	keepLostReason,
	placeLostReasonSection,
	placeStatusControl,
} from './statusChange.js'

export function addStatusControl(page) {
	placeStatusControl(page, StatusControl, readStatuses)
}

export function addLostReasonSection(page) {
	placeLostReasonSection(page, readStatuses)
}

/** The `status` field handler: a Lost status picked in the form asks for its reason. */
export function askReasonForLostStatus(page) {
	return keepLostReason(page, readStatuses(STATUS_DOCTYPES[page.doctype]), lostReasonLabels())
}

export function readStatuses(doctype) {
	return listDocuments(doctype, { fields: STATUS_FIELDS, order_by: 'position asc, creation asc', limit: 100 }).then(
		(reply) => reply.data,
	)
}
