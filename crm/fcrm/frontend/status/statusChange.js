// What the header's status control does, kept free of the desk's imports so it is unit-tested.
import { ref } from 'vue'

// The status doctypes' `color` options in CRM v1's shades, as ink tokens that follow the dark theme.
const INK = {
	black: 'text-ink-gray-9',
	gray: 'text-ink-gray-6',
	blue: 'text-ink-blue-6',
	green: 'text-ink-green-7',
	red: 'text-ink-red-6',
	pink: 'text-ink-pink-6',
	orange: 'text-ink-orange-6',
	amber: 'text-ink-amber-6',
	yellow: 'text-ink-yellow-6',
	cyan: 'text-ink-cyan-6',
	teal: 'text-ink-teal-6',
	violet: 'text-ink-violet-6',
	purple: 'text-ink-purple-6',
}

export const STATUS_FIELDS = ['name', 'color', 'position', 'type']

export const STATUS_DOCTYPES = { 'CRM Lead': 'CRM Lead Status', 'CRM Deal': 'CRM Deal Status' }

/** Adds `component` in `onRefresh`; a new record keeps `status` in its form, since a pick would insert it. */
export function placeStatusControl(page, component, readStatuses) {
	const doctype = STATUS_DOCTYPES[page.doctype]
	if (page.isNew || !doctype) return
	const statuses = page.cached(`statuses:${doctype}`, () => readStatuses(doctype))
	page.header.add(
		{
			name: 'status',
			zone: 'right',
			component,
			props: { statuses, readOnly: Boolean(page.fields.get('status')?.read_only) },
		},
		{ before: 'save' },
	)
}

/** The text colour class for a status row's `color`; gray for none or an unknown one. */
export function statusInk(color) {
	return INK[color] ?? INK.gray
}

/** The status row named `name`, or `undefined` while the statuses are not read. */
export function findStatus(statuses, name) {
	return statuses?.find((status) => status.name === name)
}

/** One pick at a time: a pick during a save would join it and be dropped. */
export function statusPicker(page, lostReasonTitle) {
	const busy = ref(false)
	async function pick(status) {
		if (busy.value) return
		busy.value = true
		try {
			await changeStatus(page, status, lostReasonTitle)
		} finally {
			busy.value = false
		}
	}
	return { busy, pick }
}

/** Writes `status` on the record and saves; a Lost one asks its reason first, and a refused save goes back. */
export async function changeStatus(page, status, lostReasonTitle) {
	if (status.name === page.doc.status) return
	const reason = await askLostReason(page, status, lostReasonTitle)
	if (!reason) return
	Object.assign(page.doc, reason, { status: status.name })
	try {
		await page.save()
	} catch (error) {
		// A conflict reload has already replaced the draft; only a pick still in it goes back.
		if (page.doc.status === status.name) page.doc.status = page.saved.status
		if (!SHOWN_IN_DIALOG.includes(error?.name)) page.toast.error(error?.message || String(error))
	}
}

/** The `status` field handler's job: a Lost status writes its reason, a cancel goes back to the saved status. */
export async function keepLostReason(page, statuses, lostReasonTitle) {
	const status = findStatus(await statuses, page.doc.status)
	const reason = await askLostReason(page, status, lostReasonTitle)
	if (reason) Object.assign(page.doc, reason)
	else page.doc.status = page.saved.status
}

/** The reason for `status`: `{}` when it is not Lost, the dialog's values, or `null` when cancelled. */
async function askLostReason(page, status, title) {
	if (status?.type !== 'Lost') return {}
	return page.dialog.form({
		title,
		doctype: page.doctype,
		fieldnames: LOST_REASON_FIELDS,
		required: ['lost_reason'],
		defaults: currentReason(page.doc),
	})
}

// The record page's own dialog has told the reader why: a save conflict, or code that does not compile.
export const SHOWN_IN_DIALOG = ['SaveConflict', 'SaveCodeErrors']

const LOST_REASON_FIELDS = ['lost_reason', 'lost_notes']

function currentReason(doc) {
	const filled = LOST_REASON_FIELDS.filter((fieldname) => doc[fieldname])
	return Object.fromEntries(filled.map((fieldname) => [fieldname, doc[fieldname]]))
}
