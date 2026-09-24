export default {
	onRefresh(page) {
		page.tabs.order(["activity", "emails"]);
	},
};
