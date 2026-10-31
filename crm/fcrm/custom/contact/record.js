import { addDealsTab, addReachPickers } from "../../frontend/contact/index.js";

export default {
	onRefresh(page) {
		addDealsTab(page);
		addReachPickers(page);
	},
};
