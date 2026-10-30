// The status control on CRM Lead's and CRM Deal's record pages: `header.status`, after the star.
import { listDocuments } from '@framework/ui/api'
import StatusControl from './StatusControl.vue'
import { STATUS_FIELDS } from './statusChange.js'

const STATUS_DOCTYPES = { 'CRM Lead': 'CRM Lead Status', 'CRM Deal': 'CRM Deal Status' }

/** Adds the control in `onRefresh`; a new record keeps `status` in its form, since a pick would insert it. */
export function addStatusControl(page) {
	const doctype = STATUS_DOCTYPES[page.doctype]
	if (page.isNew || !doctype) return
	const statuses = page.cached(`statuses:${doctype}`, () => readStatuses(doctype))
	page.header.add(
		{
			name: 'status',
			zone: 'left',
			component: StatusControl,
			props: { statuses, readOnly: Boolean(page.fields.get('status')?.read_only) },
		},
		{ after: 'favourite' },
	)
}

function readStatuses(doctype) {
	return listDocuments(doctype, { fields: STATUS_FIELDS, order_by: 'position asc', limit: 100 }).then(
		(reply) => reply.data,
	)
}
