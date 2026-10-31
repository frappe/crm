import { enableDefaultPolicy, refuseBadDefaults, startNewPolicy } from '../../../frontend/sla/slaPolicy.js'

export default {
	onOpen(page) {
		return startNewPolicy(page)
	},
	beforeSave(page) {
		refuseBadDefaults(page)
	},
	default: (page) => enableDefaultPolicy(page),
}
