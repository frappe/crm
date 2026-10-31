// CRM Lead's Convert to Deal button: `header.convert_to_deal`, after the status control.
import { getMeta } from '@framework/ui/api'
import { routeFor } from '@shell'
import { __ } from 'frappe/i18n'
import { convertLead, leadDefaults, placeConvertButton, requiredDealFields, saveBeforeConvert } from './convertToDeal.js'

export function addConvertButton(page) {
	placeConvertButton(page, {
		get label() {
			return __('Convert to Deal')
		},
		run: convertToDeal,
	})
}

async function convertToDeal(page) {
	await saveBeforeConvert(page)
	const required = requiredDealFields((await getMeta('CRM Deal')).data?.fields)
	let deal = null
	await page.dialog.form({
		title: __('Convert to Deal'),
		fields: [...linkFields(), ...required],
		defaults: leadDefaults(page.doc, required),
		submitLabel: __('Convert'),
		onSubmit: async (values) => {
			deal = await convertLead(page, values)
		},
	})
	// Routed once the dialog has closed: leaving the page mid-submit would read as a cancel.
	if (deal) await page.router.push(routeFor('CRM Deal', deal))
}

function linkFields() {
	return [
		{
			fieldname: 'organization',
			fieldtype: 'Link',
			options: 'CRM Organization',
			label: __('Organization'),
			description: __('Leave blank to create one from the lead.'),
		},
		{
			fieldname: 'contact',
			fieldtype: 'Link',
			options: 'Contact',
			label: __('Contact'),
			description: __("Leave blank to create one from the lead's person."),
		},
	]
}
