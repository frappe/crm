import { addHolidayActs } from '../../../frontend/sla/holidayList.js'

export default {
	onRefresh(page) {
		addHolidayActs(page)
	},
}
