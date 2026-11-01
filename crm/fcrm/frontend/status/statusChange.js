// A status change on Lead and Deal, from the header or a field; free of the desk's imports so it is unit-tested.
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
	const statuses = cachedStatuses(page, doctype, readStatuses)
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

/** The Side Panel's Lost Reason shows only while the status is a Lost type; the reason stays stored. */
export function placeLostReasonSection(page, readStatuses) {
	const doctype = STATUS_DOCTYPES[page.doctype]
	if (!doctype) return
	const statuses = cachedStatuses(page, doctype, readStatuses)
	showLostReasonFor(page, findStatus(statuses, page.doc.status))
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
export function statusPicker(page, labels) {
	const busy = ref(false)
	async function pick(status) {
		if (busy.value) return
		busy.value = true
		try {
			await changeStatus(page, status, labels)
		} finally {
			busy.value = false
		}
	}
	return { busy, pick }
}

/** Writes `status` on the record and saves; a Lost one asks its reason first, and a refused save goes back. */
export async function changeStatus(page, status, labels) {
	if (status.name === page.doc.status) return
	const reason = await askLostReason(page, status, labels)
	if (!reason) return
	Object.assign(page.doc, reason, { status: status.name })
	const picked = { ...page.doc }
	try {
		await page.save()
	} catch (error) {
		// A conflict reload has already replaced the draft; only a pick still in it goes back, with what `beforeSave` wrote for it.
		if (page.doc.status === status.name)
			Object.assign(page.doc, writtenSince(page.doc, picked), savedValues(page, ['status', ...Object.keys(reason)]))
		if (!SHOWN_IN_DIALOG.includes(error?.name)) page.toast.error(error?.message || String(error))
	}
}

/** The `status` field handler's job: a Lost status writes its reason, a cancel goes back to the saved status. */
export async function keepLostReason(page, statuses, labels) {
	const picked = page.doc.status
	const rows = await statuses
	// A later pick has its own handler, which asks for itself.
	if (page.doc.status !== picked) return
	const reason = await askLostReason(page, findStatus(rows, picked), labels)
	if (reason) Object.assign(page.doc, reason)
	else page.doc.status = page.saved.status
	showLostReasonFor(page, findStatus(rows, page.doc.status))
}

/** The reason for `status`: `{}` when it is not Lost, the dialog's values, or `null` when cancelled. */
async function askLostReason(page, status, labels) {
	if (!isLost(status)) return {}
	return page.dialog.form({
		...labels,
		doctype: page.doctype,
		fieldnames: LOST_REASON_FIELDS,
		required: ['lost_reason'],
		defaults: currentReason(page.doc),
	})
}

// The record page's own dialog has told the reader why: a save conflict, or code that does not compile.
export const SHOWN_IN_DIALOG = ['SaveConflict', 'SaveCodeErrors']

const LOST_REASON_FIELDS = ['lost_reason', 'lost_notes']

const LOST_REASON_SECTION = 'lost_reason_section'

function cachedStatuses(page, doctype, readStatuses) {
	return page.cached(`statuses:${doctype}`, () => readStatuses(doctype))
}

function isLost(status) {
	return status?.type === 'Lost'
}

function showLostReasonFor(page, status) {
	if (isLost(status)) page.panelSections.show(LOST_REASON_SECTION)
	else page.panelSections.hide(LOST_REASON_SECTION)
}

function savedValues(page, fieldnames) {
	return Object.fromEntries(fieldnames.map((fieldname) => [fieldname, page.saved[fieldname]]))
}

function writtenSince(doc, before) {
	const written = Object.keys(doc).filter((fieldname) => doc[fieldname] !== before[fieldname])
	return Object.fromEntries(written.map((fieldname) => [fieldname, before[fieldname]]))
}

function currentReason(doc) {
	const filled = LOST_REASON_FIELDS.filter((fieldname) => doc[fieldname])
	return Object.fromEntries(filled.map((fieldname) => [fieldname, doc[fieldname]]))
}
