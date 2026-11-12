// Lead Sync Source, Facebook Lead Form and Failed Lead Sync Log on desk v2's standard pages, free of `@shell` so it is unit-tested.
import { getMeta, runDocumentMethod } from '@framework/ui/api'
import { __ } from 'frappe/i18n'

const MAPPED_FIELD = 'questions.mapped_to_crm_field'
const NOT_MAPPABLE = [
	'Section Break',
	'Column Break',
	'Tab Break',
	'HTML',
	'Heading',
	'Button',
	'Image',
	'Attach',
	'Attach Image',
	'Table',
	'Table MultiSelect',
]

export function addSourceActs(page, routeFor) {
	// A Facebook page and form come from the token's first fetch, so a new source has none to pick.
	if (page.isNew) {
		page.fields.hide('facebook_page')
		page.fields.hide('facebook_lead_form')
		return
	}
	page.fields.update('facebook_lead_form', { link_filters: { page: page.doc.facebook_page || '' } })
	page.header.add(
		[
			{ name: 'sync_now', label: __('Sync Now'), display: 'button', run: syncNow },
			{ name: 'failed_syncs', label: __('Failed Syncs'), href: failedSyncsPath(page, routeFor) },
		],
		{ before: 'save' },
	)
}

/** A form belongs to one page, so a changed page leaves the old form behind. */
export function clearFormOnPageChange(page) {
	if (page.isNew) return
	page.doc.facebook_lead_form = ''
	page.fields.update('facebook_lead_form', { link_filters: { page: page.doc.facebook_page || '' } })
}

function failedSyncsPath(page, routeFor) {
	return page.router.resolve(routeFor('Failed Lead Sync Log', null, { query: { source: page.docname } })).fullPath
}

async function syncNow(page) {
	// The server syncs the saved source.
	if (!(await page.save())) return
	try {
		await runDocumentMethod(page.doctype, page.docname, 'sync_leads', {}, { nullable: true })
	} catch (error) {
		page.toast.error(error?.message || String(error))
		return
	}
	page.toast.success(__('Lead sync initiated.'))
}

export function addMappingOptions(page) {
	// `cached` answers at once, and the replay runs again when the fields arrive.
	const fields = page.cached('lead_sync:crm_lead_fields', readLeadFields)
	if (!fields) return
	page.fields.update(MAPPED_FIELD, { options: fields, placeholder: __('Not Synced') })
}

async function readLeadFields() {
	const meta = await getMeta('CRM Lead')
	return mappableFields(meta.data?.fields)
}

/** The CRM Lead fields a form question may fill, as `{ value, label }` pairs. */
export function mappableFields(metaFields) {
	return (metaFields ?? [])
		.filter((field) => !NOT_MAPPABLE.includes(field.fieldtype) && !field.read_only && !field.hidden)
		.map((field) => ({ value: field.fieldname, label: field.label || field.fieldname }))
}

export function addRetryAct(page) {
	if (page.doc.type === 'Synced') return
	page.header.add({ name: 'retry_sync', label: __('Retry Sync'), display: 'button', run: retrySync }, { before: 'save' })
}

async function retrySync(page) {
	let lead
	try {
		lead = (await runDocumentMethod(page.doctype, page.docname, 'retry_sync')).data
	} catch (error) {
		page.toast.error(error?.message || String(error))
		return
	}
	page.toast.success(__('Sync successful, CRM Lead: {0}', [lead?.name ?? '']))
	await page.refresh()
}
