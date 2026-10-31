// A condition builder over a record's JSON and Python condition pair, kept free of the desk's imports so it is unit-tested.
import { __ } from 'frappe/i18n'

export function isLegacy(doc, pair) {
	return Boolean(doc?.[pair.python]) && !doc?.[pair.json]
}

export function usesBuilder(page, pair) {
	if (page.doc[pair.json]) return true
	// The saved Python too: emptying the Python field to retype it must not swap it for the builder.
	return page.app === 'crm' && !page.doc[pair.python] && !page.saved?.[pair.python]
}

// A new record has no record rights before its insert, which checks create.
export function canEdit(page) {
	return Boolean(page.isNew || page.perms?.write)
}

export function placeConditions(page, pairs, { builder, legacyNote }) {
	for (const pair of pairs) {
		if (usesBuilder(page, pair)) showBuilder(page, pair, builder)
		if (page.app === 'crm') placeLegacyNote(page, pair, legacyNote)
	}
}

// Empties the Python, so a save never keeps the old condition running.
export function switchToBuilder(page, pair) {
	page.doc[pair.json] = '[]'
	page.doc[pair.python] = ''
	page.refresh()
}

export async function keepExpression(page, pair, { fieldsOf, compile }) {
	if (!page.doc[pair.json]) return
	const fields = await fieldsOf(page.doc[pair.doctypeField])
	// Read after the wait, so a later edit's JSON is the one compiled.
	if (page.doc[pair.json]) page.doc[pair.python] = compile(page.doc[pair.json], fields, pair)
}

export async function keepExpressions(page, pairs, compiler) {
	await Promise.all(pairs.map((pair) => keepExpression(page, pair, compiler)))
}

// Only what changed: reading the JSON drops what the builder cannot model, so an untouched pair keeps its Python.
export function keepChangedExpressions(page, pairs, compiler) {
	const changed = pairs.filter(
		(pair) =>
			page.doc[pair.doctypeField] !== page.saved?.[pair.doctypeField] ||
			page.doc[pair.json] !== page.saved?.[pair.json],
	)
	return keepExpressions(page, changed, compiler)
}

// The Python is hidden under the builder, so its errors are named on the JSON field.
export function refuseIncompleteConditions(page, pairs) {
	for (const pair of pairs) {
		if (!usesBuilder(page, pair)) continue
		const rows = parseConditions(page.doc[pair.json]).length
		if (pair.required && !rows) throw page.fields.setError(pair.json, __('Add at least one condition'))
		// A row the compiler cannot express, such as `like` with no value, compiles to nothing.
		if (rows && !page.doc[pair.python]) throw page.fields.setError(pair.json, __('Complete each condition'))
	}
}

function showBuilder(page, pair, builder) {
	const doctype = page.doc[pair.doctypeField]
	page.fields.update(pair.json, {
		hidden: false,
		label: pair.label(),
		description: doctype ? pair.description(doctype) : pair.noDoctype(),
		component: builder,
		props: { page, python: pair.python, required: pair.required, doctypeField: pair.doctypeField },
	})
	page.fields.update(pair.python, { hidden: true })
}

function placeLegacyNote(page, pair, legacyNote) {
	const inUse = isLegacy(page.doc, pair)
	if (!inUse && !(isLegacy(page.saved, pair) && usesBuilder(page, pair))) return
	page.form.add(
		{ name: `legacy_${pair.python}`, component: legacyNote, props: { pair } },
		{ before: inUse ? pair.python : pair.json },
	)
}

export function expressionOptions(fields, pair) {
	return { fields, fieldPrefix: pair.fieldPrefix }
}

export function parseConditions(json) {
	try {
		const conditions = JSON.parse(json || '[]')
		return Array.isArray(conditions) ? conditions : []
	} catch {
		return []
	}
}
