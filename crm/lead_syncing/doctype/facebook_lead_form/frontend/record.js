import { addMappingOptions } from '../../../../fcrm/frontend/lead_sync/leadSync.js'

export default {
	onRefresh(page) {
		addMappingOptions(page)
	},
}
