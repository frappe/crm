// What CRM adds to Assignment Rule's record page, kept free of the desk's imports so it is unit-tested.
import { __ } from 'frappe/i18n'

/** Each condition CRM edits as JSON, beside the Python that `safe_eval` runs. */
export const CONDITIONS = [
	{
		json: 'assign_condition_json',
		python: 'assign_condition',
		required: true,
		label: () => __('Assign Condition'),
		description: (doctype) => __('Choose which {0} are affected by this assignment rule.', [doctype]),
	},
	{
		json: 'unassign_condition_json',
		python: 'unassign_condition',
		required: false,
		label: () => __('Unassign Condition'),
		description: (doctype) => __('Choose which {0} are affected by this un-assignment rule.', [doctype]),
	},
]

const ALL_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

/** A condition written in Python, which the builder cannot read: Python and no JSON. */
export function isLegacy(doc, pair) {
	return Boolean(doc?.[pair.python]) && !doc?.[pair.json]
}

/** The builder edits a rule that holds the JSON; on `/apps/crm`, also one with no condition yet. */
export function usesBuilder(page, pair) {
	if (page.doc[pair.json]) return true
	return page.app === 'crm' && !page.doc[pair.python]
}

/** Draws each condition the builder edits in its JSON field's slot, and the Python one's note on `/apps/crm`. */
export function placeConditions(page, { builder, legacyNote }) {
	for (const pair of CONDITIONS) {
		if (usesBuilder(page, pair)) showBuilder(page, pair, builder)
		if (page.app === 'crm') placeLegacyNote(page, pair, legacyNote)
	}
}

/** Starts the builder on a Python condition; the Python goes, so a save never keeps it running. */
export function switchToBuilder(page, pair) {
	page.doc[pair.json] = '[]'
	page.doc[pair.python] = ''
	page.refresh()
}

/** Recompiles the Python from the JSON, with the target's fieldtypes; a rule with no JSON keeps its Python. */
export async function keepExpression(page, pair, { fieldsOf, compile }) {
	if (!page.doc[pair.json]) return
	const fields = await fieldsOf(page.doc.document_type)
	// Read after the wait, so a later edit's JSON is the one compiled.
	if (page.doc[pair.json]) page.doc[pair.python] = compile(page.doc[pair.json], fields)
}

export async function keepExpressions(page, compiler) {
	await Promise.all(CONDITIONS.map((pair) => keepExpression(page, pair, compiler)))
}

/** A new rule on `/apps/crm` runs on every day, as CRM v1's did. */
export function startOnEveryDay(page) {
	if (page.app !== 'crm' || !page.isNew || page.doc.assignment_days?.length) return
	page.doc.assignment_days = ALL_DAYS.map((day) => ({ day }))
}

/** Refuses an empty assign condition in the builder: the Python it compiles to is mandatory, and hidden. */
export function refuseEmptyCondition(page) {
	const [assign] = CONDITIONS
	if (usesBuilder(page, assign) && !parseConditions(page.doc[assign.json]).length)
		throw page.fields.setError(assign.json, __('Add at least one condition'))
}

function showBuilder(page, pair, builder) {
	const doctype = page.doc.document_type
	page.fields.update(pair.json, {
		hidden: false,
		label: pair.label(),
		description: doctype ? pair.description(doctype) : __('Set the document type to add conditions.'),
		component: builder,
		props: { page, python: pair.python, required: pair.required },
	})
	page.fields.update(pair.python, { hidden: true })
}

// Above the Python while it is in use; above the builder until the switch is saved, naming what it replaces.
function placeLegacyNote(page, pair, legacyNote) {
	const inUse = isLegacy(page.doc, pair)
	if (!inUse && !(isLegacy(page.saved, pair) && usesBuilder(page, pair))) return
	page.form.add(
		{ name: `legacy_${pair.python}`, component: legacyNote, props: { pair } },
		{ before: inUse ? pair.python : pair.json },
	)
}

/** The stored array, or `[]` for an empty or unreadable one. */
export function parseConditions(json) {
	try {
		const conditions = JSON.parse(json || '[]')
		return Array.isArray(conditions) ? conditions : []
	} catch {
		return []
	}
}
