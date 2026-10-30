// What the header's status control does, kept free of the desk's imports so it is unit-tested.

// The status doctypes' `color` options in the shades CRM v1 drew; the ink tokens flip in dark mode.
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

/** The text colour class for a status row's `color`; gray for none or an unknown one. */
export function statusInk(color) {
	return INK[color] ?? INK.gray
}

/** The status row named `name`, or `undefined` while the statuses are not read. */
export function findStatus(statuses, name) {
	return statuses?.find((status) => status.name === name)
}

/** Writes `status` on the record and saves; a failed save puts the old status back and shows why. */
export async function changeStatus(page, status) {
	const previous = page.doc.status
	if (status.name === previous) return
	page.doc.status = status.name
	try {
		await page.save()
	} catch (error) {
		page.doc.status = previous
		page.toast.error(saveError(error))
	}
}

/** A failed save's first server message, else its own. */
export function saveError(error) {
	return error?.messages?.[0] || error?.message || String(error)
}
