// What CRM Lead's Convert to Deal button does, kept free of the desk's imports so it is unit-tested.

export const CONVERT_METHOD = 'crm.fcrm.doctype.crm_lead.crm_lead.convert_to_deal'

// The dialog's own Links: blank, the server creates the organization and the contact from the lead.
export const LINK_FIELDS = ['organization', 'contact']

// A dialog field list cannot draw a grid or a layout break.
const NOT_INPUTS = ['Table', 'Table MultiSelect', 'Section Break', 'Column Break', 'Tab Break', 'HTML', 'Button']

// Deal fields filled from a lead field of another name; `status` and `organization` are not copied.
const FROM_LEAD = { deal_owner: 'lead_owner' }
const NOT_FROM_LEAD = ['status', 'organization']

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
		.map(toDialogField)
}

/** The lead's values for `fields`, so a deal field the lead already holds is not typed twice. */
export function leadDefaults(lead, fields) {
	const defaults = {}
	for (const { fieldname } of fields) {
		if (NOT_FROM_LEAD.includes(fieldname)) continue
		const value = lead[FROM_LEAD[fieldname] ?? fieldname]
		if (value != null && value !== '') defaults[fieldname] = value
	}
	return defaults
}

/** Saves the lead's edits first, since the server converts the saved lead. */
export async function saveBeforeConvert(page) {
	if (page.isDirty) await page.save()
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

function toDialogField(field) {
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

// An empty value would overwrite what the server copies from the lead.
function filled(values) {
	return Object.fromEntries(Object.entries(values).filter(([, value]) => value != null && value !== ''))
}
