import { listDocuments } from '@framework/ui/api'
import { __ } from 'frappe/i18n'

const WORKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
const ONE_HOUR = 60 * 60

// The server evaluates the condition with the record as `doc` (`get_context`).
export const SLA_CONDITION = {
	json: 'condition_json',
	python: 'condition',
	doctypeField: 'apply_on',
	fieldPrefix: 'doc',
	required: false,
	label: () => __('Condition'),
	description: (doctype) => __('Choose which {0} this SLA applies to.', [doctype]),
	noDoctype: () => __('Set Apply On to add conditions.'),
}

export async function startNewPolicy(page) {
	if (!page.isNew) return
	if (!page.doc.working_hours?.length) page.doc.working_hours = officeHours()
	if (page.doc.priorities?.length) return
	const priorities = await statusPriorities()
	if (!page.doc.priorities?.length) page.doc.priorities = priorities
}

export function enableDefaultPolicy(page) {
	if (page.doc.default) page.doc.enabled = 1
}

export function refuseBadDefaults(page) {
	if (page.doc.default && !page.doc.enabled)
		throw page.fields.setError('enabled', __('An SLA set as default cannot be disabled'))
	const defaults = (page.doc.priorities ?? []).filter((row) => row.default_priority)
	if (defaults.length > 1)
		throw page.fields.setError('priorities', __('There can only be one default priority'))
}

// The first created status (Open) is the default: SLA timing reads the default as awaiting a response.
async function statusPriorities() {
	const { data } = await listDocuments('CRM Communication Status', {
		fields: ['name'],
		order_by: 'creation asc',
		limit: 100,
	})
	return data.map(({ name }, index) => ({
		priority: name,
		first_response_time: ONE_HOUR,
		default_priority: index === 0 ? 1 : 0,
	}))
}

function officeHours() {
	return WORKDAYS.map((workday) => ({ workday, start_time: '09:00:00', end_time: '17:00:00' }))
}
