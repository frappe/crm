// What CRM adds to Assignment Rule's record page, kept free of the desk's imports so it is unit-tested.
import { __ } from 'frappe/i18n'

const noDoctype = () => __('Set the document type to add conditions.')

export const CONDITIONS = [
	{
		json: 'assign_condition_json',
		python: 'assign_condition',
		doctypeField: 'document_type',
		required: true,
		label: () => __('Assign Condition'),
		description: (doctype) => __('Choose which {0} are affected by this assignment rule.', [doctype]),
		noDoctype,
	},
	{
		json: 'unassign_condition_json',
		python: 'unassign_condition',
		doctypeField: 'document_type',
		required: false,
		label: () => __('Unassign Condition'),
		description: (doctype) => __('Choose which {0} are affected by this un-assignment rule.', [doctype]),
		noDoctype,
	},
]

const ALL_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

export function startOnEveryDay(page) {
	if (page.app !== 'crm' || !page.isNew || page.doc.assignment_days?.length) return
	page.doc.assignment_days = ALL_DAYS.map((day) => ({ day }))
}
