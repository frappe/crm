// What the deal and lead Activity tab reads and draws for its Task, Note and Call Log rows, kept free of the desk's imports so it is unit-tested.
import { __ } from 'frappe/i18n'

const GET_LIST_METHOD = 'frappe.client.get_list'
const HAS_PERMISSION_METHOD = 'frappe.client.has_permission'
// The newest rows of each source.
const ROWS_PER_SOURCE = 100

const SOURCES = [
	{ doctype: 'CRM Task', key: 'task', fields: ['name', 'title', 'status', 'priority', 'due_date', 'creation'] },
	{ doctype: 'FCRM Note', key: 'note', fields: ['name', 'title', 'content', 'creation'] },
	{
		doctype: 'CRM Call Log',
		key: 'call',
		fields: ['name', 'type', 'status', 'from', 'to', 'duration', 'start_time', 'creation'],
	},
]

/** Where the tab's records may be referenced from: the page's own record, and a deal's lead, whose history the deal inherits. */
export async function referenceScope(page) {
	const scope = { doctypes: [page.doctype], names: [page.docname] }
	const lead = page.doc?.lead
	if (lead && (await canReadLead(page, lead))) {
		scope.doctypes.push('CRM Lead')
		scope.names.push(lead)
	}
	return scope
}

/** The one `page.cached` fetcher: every source's newest rows for the scope; a source the user cannot read draws none. */
export function fetchActivityRows(page) {
	return async () => {
		const { doctypes, names } = await referenceScope(page)
		const lists = await Promise.all(SOURCES.map((source) => readSource(page, source, doctypes, names)))
		return SOURCES.flatMap((source, index) => lists[index].map((row) => ({ ...row, source })))
	}
}

async function canReadLead(page, lead) {
	const reply = await page
		.call(HAS_PERMISSION_METHOD, { doctype: 'CRM Lead', docname: lead })
		.catch(() => ({ has_permission: false }))
	return Boolean(reply?.has_permission)
}

// Only a refusal is an empty list: any other failure rejects, so the page keeps the rows it holds.
function readSource(page, source, doctypes, names) {
	return page
		.call(GET_LIST_METHOD, {
			doctype: source.doctype,
			fields: source.fields,
			filters: { reference_doctype: ['in', doctypes], reference_docname: ['in', names] },
			order_by: 'creation desc',
			limit_page_length: ROWS_PER_SOURCE,
		})
		.catch((error) => {
			if (isPermissionError(error)) return []
			throw error
		})
}

export function isPermissionError(error) {
	return error?.status === 403 || error?.exc_type === 'PermissionError' || /not permitted/i.test(error?.message ?? '')
}

/** A `page.activity.add` item for one record, placed by its creation (a call, by its start). */
export function activityItem(row, component) {
	const { source } = row
	const timestamp = (row.start_time || row.creation).slice(0, 19)
	return {
		name: `${source.key}:${row.name}`,
		timestamp,
		component,
		props: { doctype: source.doctype, record: String(row.name), timestamp, ...ROW_PROPS[source.key](row) },
	}
}

const ROW_PROPS = {
	task: (row) => ({
		icon: 'lucide-circle-check-big',
		label: __('Task'),
		title: row.title,
		detail: [row.status, row.priority, row.due_date && __('Due {0}', [row.due_date.slice(0, 10)])]
			.filter(Boolean)
			.join(' · '),
	}),
	note: (row) => ({
		icon: 'lucide-notebook-pen',
		label: __('Note'),
		title: row.title || plainText(row.content),
		detail: '',
	}),
	call: (row) => ({
		icon: row.type === 'Incoming' ? 'lucide-phone-incoming' : 'lucide-phone-outgoing',
		label: row.type === 'Incoming' ? __('Incoming call') : __('Outgoing call'),
		title: [row.from, row.to].filter(Boolean).join(' → '),
		detail: [row.status, row.duration && durationText(row.duration)].filter(Boolean).join(' · '),
	}),
}

function plainText(html) {
	return (html ?? '').replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()
}

function durationText(seconds) {
	const minutes = Math.floor(seconds / 60)
	return minutes ? `${minutes}m ${seconds % 60}s` : `${seconds}s`
}
