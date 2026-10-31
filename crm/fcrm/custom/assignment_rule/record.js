import { CONDITIONS, startOnEveryDay } from '../../frontend/assignment_rule/assignmentRule.js'
import {
	addConditionBuilders,
	keepChangedConditionsInStep,
	keepConditionInStep,
	keepConditionsInStep,
	refuseIncompleteConditions,
} from '../../frontend/conditions/index.js'

const [assign, unassign] = CONDITIONS

export default {
	onRefresh(page) {
		addConditionBuilders(page, CONDITIONS)
	},
	onOpen(page) {
		startOnEveryDay(page)
	},
	async beforeSave(page) {
		await keepChangedConditionsInStep(page, CONDITIONS)
		refuseIncompleteConditions(page, CONDITIONS)
	},
	document_type: (page) => keepConditionsInStep(page, CONDITIONS),
	assign_condition_json: (page) => keepConditionInStep(page, assign),
	unassign_condition_json: (page) => keepConditionInStep(page, unassign),
}
