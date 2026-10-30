// The status control on CRM Lead's and CRM Deal's record pages: `header.status`, before Save.
import { listDocuments } from '@framework/ui/api'
import StatusControl from './StatusControl.vue'
import { STATUS_FIELDS, placeStatusControl } from './statusChange.js'

export function addStatusControl(page) {
	placeStatusControl(page, StatusControl, readStatuses)
}

function readStatuses(doctype) {
	return listDocuments(doctype, { fields: STATUS_FIELDS, order_by: 'position asc', limit: 100 }).then(
		(reply) => reply.data,
	)
}
