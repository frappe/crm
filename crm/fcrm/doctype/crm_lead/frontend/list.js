import { callRowAction } from "../../../frontend/telephony/callRowAction.js";

export default {
	onRefresh(page) {
		page.rowActions.add(callRowAction);
	},
};
