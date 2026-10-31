// Assignment Rule's condition builder on CRM's JSON fields, wired to the desk.
import { watch } from 'vue'
import { fromFrappeConditions, toConditionExpression } from '@framework/ui/ConditionBuilder'
import { useDoctypeMeta } from '@framework/ui/useDoctypeMeta'
import ConditionsField from './ConditionsField.vue'
import LegacyCondition from './LegacyCondition.vue'
import { keepExpression, keepExpressions, parseConditions, placeConditions } from './assignmentRule.js'

export { CONDITIONS, refuseEmptyCondition, startOnEveryDay } from './assignmentRule.js'

const compiler = {
	fieldsOf: targetFields,
	compile: (json, fields) => toConditionExpression(fromFrappeConditions(parseConditions(json)), { fields }),
}

export function addConditionBuilders(page) {
	placeConditions(page, { builder: ConditionsField, legacyNote: LegacyCondition })
}

export function keepConditionInStep(page, pair) {
	return keepExpression(page, pair, compiler)
}

export function keepConditionsInStep(page) {
	return keepExpressions(page, compiler)
}

/** The target's fields, from the meta the builder already read; `undefined` when it cannot be read. */
async function targetFields(doctype) {
	if (!doctype) return undefined
	const { meta, loading } = useDoctypeMeta(doctype)
	if (loading.value) await settled(loading)
	return meta.value?.fields
}

function settled(loading) {
	return new Promise((resolve) => {
		const stop = watch(loading, (now) => {
			if (now) return
			stop()
			resolve()
		})
	})
}
