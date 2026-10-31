// CRM Holiday List's two Button fields as header acts, since a Button field does nothing on desk v2 yet (frappe#46008).
import { runMethod } from '@framework/ui/api'
import { __ } from 'frappe/i18n'

const NEEDED = ['from_date', 'to_date', 'weekly_off']

export function addHolidayActs(page) {
	page.fields.hide('add_to_holidays')
	page.fields.hide('clear_table')
	// A new record has no record rights before its insert, which checks create (frappe#46033).
	const right = page.isNew ? undefined : 'write'
	page.header.add(
		[
			{ name: 'add_to_holidays', label: __('Add to Holidays'), display: 'button', right, run: addWeeklyOffs },
			{ name: 'clear_table', label: __('Clear Table'), right, run: clearHolidays },
		],
		{ before: 'save' },
	)
}

export async function addWeeklyOffs(page) {
	const missing = NEEDED.filter((fieldname) => !page.doc[fieldname])
	for (const fieldname of missing) page.fields.setError(fieldname, __('Set this to add the weekly offs'))
	if (missing.length) return

	const sent = [...(page.doc.holidays ?? [])]
	const { docs } = await runMethod(
		'run_doc_method',
		{
			// Without `__islocal` the server reads a new list from the database and answers 404.
			document: { ...page.doc, holidays: sent, doctype: page.doctype, __islocal: page.isNew ? 1 : 0 },
			method: 'get_weekly_off_dates',
		},
		{ nullable: true },
	)
	// The server appends after the rows it was sent; rows edited meanwhile are kept.
	const added = (docs?.[0]?.holidays ?? []).slice(sent.length)
	page.doc.holidays = [
		...(page.doc.holidays ?? []),
		...added.map(({ date, description, weekly_off }) => ({ date, description, weekly_off })),
	]
}

export function clearHolidays(page) {
	page.doc.holidays = []
}
