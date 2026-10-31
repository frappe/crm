import { watch } from 'vue'
import { fromFrappeConditions, toConditionExpression } from '@framework/ui/ConditionBuilder'
import { useDoctypeMeta } from '@framework/ui/useDoctypeMeta'
import ConditionsField from './ConditionsField.vue'
import LegacyCondition from './LegacyCondition.vue'
import {
	keepChangedExpressions,
	keepExpressions,
	keepExpression,
	parseConditions,
	placeConditions,
} from './conditions.js'

export { refuseIncompleteConditions } from './conditions.js'

const compiler = {
	fieldsOf: targetFields,
	compile: (json, fields, { fieldPrefix }) =>
		toConditionExpression(fromFrappeConditions(parseConditions(json)), { fields, fieldPrefix }),
}

export function addConditionBuilders(page, pairs) {
	placeConditions(page, pairs, { builder: ConditionsField, legacyNote: LegacyCondition })
}

export function keepConditionInStep(page, pair) {
	return keepExpression(page, pair, compiler)
}

export function keepConditionsInStep(page, pairs) {
	return keepExpressions(page, pairs, compiler)
}

export function keepChangedConditionsInStep(page, pairs) {
	return keepChangedExpressions(page, pairs, compiler)
}

// Check and numeric fields compile from their fieldtype; `undefined` falls back to reading the value.
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
