import { addStatusControl } from "../../../frontend/status/index.js";

export default {
	onRefresh(page) {
		page.tabs.order(["activity", "emails"]);
		addStatusControl(page);
	},
};
