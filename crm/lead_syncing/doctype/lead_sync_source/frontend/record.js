import { routeFor } from '@shell'
import { addSourceActs, clearFormOnPageChange } from '../../../../fcrm/frontend/lead_sync/leadSync.js'

export default {
	onRefresh(page) {
		addSourceActs(page, routeFor)
	},
	facebook_page: (page) => clearFormOnPageChange(page),
}
