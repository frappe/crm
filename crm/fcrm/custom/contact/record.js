import { addDealsTab } from "../../frontend/contact/index.js";

export default {
	onRefresh(page) {
		addDealsTab(page);
	},
};
