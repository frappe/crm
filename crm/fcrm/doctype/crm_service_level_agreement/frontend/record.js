import {
	addConditionBuilders,
	keepChangedConditionsInStep,
	keepConditionInStep,
	keepConditionsInStep,
	refuseIncompleteConditions,
} from '../../../frontend/conditions/index.js'
import {
	SLA_CONDITION,
	enableDefaultPolicy,
	refuseBadDefaults,
	startNewPolicy,
} from '../../../frontend/sla/slaPolicy.js'

const CONDITIONS = [SLA_CONDITION]

export default {
	onRefresh(page) {
		addConditionBuilders(page, CONDITIONS)
	},
	onOpen(page) {
		return startNewPolicy(page)
	},
	async beforeSave(page) {
		await keepChangedConditionsInStep(page, CONDITIONS)
		refuseIncompleteConditions(page, CONDITIONS)
		refuseBadDefaults(page)
	},
	default: (page) => enableDefaultPolicy(page),
	apply_on: (page) => keepConditionsInStep(page, CONDITIONS),
	condition_json: (page) => keepConditionInStep(page, SLA_CONDITION),
}
