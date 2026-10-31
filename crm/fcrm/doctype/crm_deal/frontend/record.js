import { addEnrichItem } from "../../../frontend/enrich/index.js";
import { addStatusControl, askReasonForLostStatus } from "../../../frontend/status/index.js";

export default {
	onRefresh(page) {
		page.tabs.order(["activity", "emails"]);
		addStatusControl(page);
		addEnrichItem(page);
	},
	status: askReasonForLostStatus,
};
