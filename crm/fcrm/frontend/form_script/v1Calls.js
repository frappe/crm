// What the v1 calls section shows, kept free of the desk's imports so it is unit-tested.

export const GUIDE = 'https://github.com/frappe/crm/blob/desk-v2/docs/form-scripts-on-desk-v2.md'

const NO_COUNTERPART = 'No counterpart'
const ISSUE = /^https:\/\/github\.com\/([\w.-]+\/[\w.-]+)\/issues\/(\d+)$/

export function placeCallsSection(page, section) {
	if (page.isNew) return
	page.panelSections.add({
		name: 'v1_calls',
		opened: true,
		...section,
		props: { calls: callRows(page.doc.v1_calls) },
	})
}

export function callRows(calls = []) {
	return calls.map((call) => ({
		name: call.name,
		line: call.line,
		call: call.v1_call,
		verb: call.verb === NO_COUNTERPART ? null : call.verb,
		guide: `${GUIDE}#${call.catalog_key}`,
		gap: call.gap ? gapOf(call.gap) : null,
	}))
}

function gapOf(gap) {
	const issue = gap.match(ISSUE)
	return issue ? { url: gap, label: `${issue[1]}#${issue[2]}` } : { label: gap }
}
