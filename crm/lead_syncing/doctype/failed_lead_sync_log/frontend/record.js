import { addRetryAct } from '../../../../fcrm/frontend/lead_sync/leadSync.js'

export default {
	onRefresh(page) {
		addRetryAct(page)
	},
}
