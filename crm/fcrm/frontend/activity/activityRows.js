// What the deal and lead Activity tab reads and draws for its Task, Note and Call Log rows, kept free of the desk's imports so it is unit-tested.
import { __ } from 'frappe/i18n'

const GET_LIST_METHOD = 'frappe.client.get_list'

const SOURCES = [
	{ doctype: 'CRM Task', key: 'task', fields: ['name', 'title', 'status', 'priority', 'due_date', 'creation'] },
	{ doctype: 'FCRM Note', key: 'note', fields: ['name', 'title', 'content', 'creation'] },
	{
		doctype: 'CRM Call Log',
		key: 'call',
		fields: ['name', 'type', 'status', 'from', 'to', 'duration', 'start_time', 'creation'],
	},
]

/** The records the tab lists: the page's own, and a deal's lead, whose history the deal inherits. */
export function referenceNames(page) {
	return [page.docname, page.doc?.lead].filter(Boolean)
}

/** One `page.cached` fetch: every source's rows for the reference names; a source the user cannot read draws none. */
export function fetchActivityRows(page, names) {
	return async () => {
		const lists = await Promise.all(
			SOURCES.map((source) =>
				page
					.call(GET_LIST_METHOD, {
						doctype: source.doctype,
						fields: source.fields,
						filters: { reference_docname: ['in', names] },
						limit_page_length: 0,
					})
					.catch(() => []),
			),
		)
		return SOURCES.flatMap((source, index) => (lists[index] ?? []).map((row) => ({ ...row, source })))
	}
}

/** A `page.activity.add` item for one record, placed by its creation (a call, by its start). */
export function activityItem(row, component) {
	const { source } = row
	const timestamp = (row.start_time || row.creation).slice(0, 19)
	return {
		name: `${source.key}:${row.name}`,
		timestamp,
		component,
		props: { doctype: source.doctype, record: row.name, timestamp, ...ROW_PROPS[source.key](row) },
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
