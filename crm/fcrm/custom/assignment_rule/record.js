import {
	CONDITIONS,
	addConditionBuilders,
	keepChangedConditionsInStep,
	keepConditionInStep,
	keepConditionsInStep,
	refuseIncompleteConditions,
	startOnEveryDay,
} from '../../frontend/assignment_rule/index.js'

const [assign, unassign] = CONDITIONS

export default {
	onRefresh(page) {
		addConditionBuilders(page)
	},
	onOpen(page) {
		startOnEveryDay(page)
	},
	async beforeSave(page) {
		await keepChangedConditionsInStep(page)
		refuseIncompleteConditions(page)
	},
	document_type: (page) => keepConditionsInStep(page),
	assign_condition_json: (page) => keepConditionInStep(page, assign),
	unassign_condition_json: (page) => keepConditionInStep(page, unassign),
}
