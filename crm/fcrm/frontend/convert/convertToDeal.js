// What CRM Lead's Convert to Deal button does, kept free of the desk's imports so it is unit-tested.
import { SHOWN_IN_DIALOG } from '../status/statusChange.js'

export const CONVERT_METHOD = 'crm.fcrm.doctype.crm_lead.crm_lead.convert_to_deal'

const LINK_FIELDS = ['organization', 'contact']

// A dialog field list cannot draw a grid or a layout break.
const NOT_INPUTS = ['Table', 'Table MultiSelect', 'Section Break', 'Column Break', 'Tab Break', 'HTML', 'Button']

const FROM_LEAD = { deal_owner: 'lead_owner' }
// A lead status is not a CRM Deal Status name.
const NOT_FROM_LEAD = ['status']

/** Adds the button after the status control; a new lead has nothing to convert yet. */
export function placeConvertButton(page, item) {
	if (page.isNew) return
	page.header.add(
		{ name: 'convert_to_deal', zone: 'right', display: 'button', right: 'write', ...item },
		{ after: 'status' },
	)
}

/** The CRM Deal fields a new deal needs that nothing fills: `reqd` without a default, as CRM v1 asked. */
export function requiredDealFields(metaFields) {
	return (metaFields ?? [])
		.filter((field) => field.reqd && !field.default)
		.filter((field) => !LINK_FIELDS.includes(field.fieldname) && !NOT_INPUTS.includes(field.fieldtype))
}

/** A meta field as a `page.dialog.form` field, forced mandatory. */
export function toDialogField(field) {
	return {
		fieldname: field.fieldname,
		fieldtype: field.fieldtype,
		label: field.label,
		options: field.options,
		reqd: 1,
		depends_on: field.depends_on,
		description: field.description,
	}
}

/** The lead's values for the deal's `fields`, matched as the server copies them, so none is typed twice. */
export function leadDefaults(lead, leadFields, fields) {
	const defaults = {}
	for (const field of fields) {
		if (NOT_FROM_LEAD.includes(field.fieldname)) continue
		const value = lead[leadFieldname(field, leadFields ?? [])]
		if (value != null && value !== '') defaults[field.fieldname] = value
	}
	return defaults
}

/** Saves the lead's edits, since the server converts the saved lead; false, with the reason shown, when refused. */
export async function saveLead(page) {
	try {
		await page.save()
		return true
	} catch (error) {
		if (!SHOWN_IN_DIALOG.includes(error?.name)) page.toast.error(error?.message || String(error))
		return false
	}
}

/** Converts the lead with the dialog's values; resolves with the new deal's name. */
export function convertLead(page, values) {
	const { organization, contact, ...deal } = values
	return page.call(CONVERT_METHOD, {
		lead: page.docname,
		deal: filled(deal),
		existing_organization: organization || null,
		existing_contact: contact || null,
	})
}

// The server's `get_deal_fieldname`, read the other way: a custom field matches one custom lead field by label and type.
function leadFieldname(dealField, leadFields) {
	if (FROM_LEAD[dealField.fieldname]) return FROM_LEAD[dealField.fieldname]
	if (leadFields.some((field) => field.fieldname === dealField.fieldname)) return dealField.fieldname
	if (!isCustom(dealField)) return null
	const matches = leadFields.filter(
		(field) => isCustom(field) && field.label === dealField.label && field.fieldtype === dealField.fieldtype,
	)
	return matches.length === 1 ? matches[0].fieldname : null
}

function isCustom(field) {
	return Boolean(field.is_custom_field || field.custom || field.fieldname?.startsWith('custom_'))
}

// An empty value would overwrite what the server copies from the lead.
function filled(values) {
	return Object.fromEntries(Object.entries(values).filter(([, value]) => value != null && value !== ''))
}
